from squidmusicweb.models import MusicLibrary, Song, Album
from datetime import datetime
import xml.parsers.expat as expat
import iso8601
import mutagen
import os, os.path
import urllib
import json

class DoneException(Exception) :
    def __str__(self) :
        return "Done"

def doLibrarySynchronization(libraries) :
    message = ""
    successful = 0
    for library in libraries :
        if library.library_type == "iTunes" :
            succ, msg = doiTunesSync(library)
            if succ :
                message += "<p>Synchronized iTunes library \""+library.library_name+"\".</p>" + msg
                successful += 1
            else :
                message += "<p>Did not synchronize iTunes library \""+library.library_name+"\".</p>" + msg
        elif library.library_type == "directory" :
            succ, msg = doDirectorySync(library)
            if succ :
                message += "<p>Synchronized directory \""+library.library_name+"\".</p>" + msg
                successful += 1
            else :
                message += "<p>Did not synchronize directory \""+library.library_name+"\".</p>" + msg
        elif library.library_type == "external" :
            succ, msg = doExternalSync(library)
            if succ :
                message += "<p>Synchronized with external library \""+library.library_name+"\".</p>" + msg
                successful += 1
            else :
                message += "<p>Did not synchronize with external library \""+library.library_name+"\".</p>" + msg
    return ("<p>%s/%s libraries were synchronized.</p>" % (successful, len(libraries))) + message

def doiTunesSync(lib) :
#    try :
        Song.objects.filter(song_album__album_library__id = lib.id).update(song_synchronized = False)
        Album.objects.filter(album_library__id = lib.id).update(album_synchronized = False)

        xmlparser = expat.ParserCreate()
        isync = iTunesSyncer(xmlparser, lib)
        try :
            xmlparser.ParseFile(open(lib.library_location, 'r'))
        except DoneException :
            pass # we want to get here.  We hit playlists

        Song.objects.filter(song_album__album_library__id = lib.id, song_synchronized = False).delete()
        Album.objects.filter(album_library__id = lib.id, album_synchronized = False).delete()

        lib.last_synchronized = datetime.now()
        lib.save()
        message = ""
        if len(isync.skippedSongs) > 0 :
            message += "<p>Skipped songs:</p><ul>"
            for filename, reason in isync.skippedSongs :
                message += "<li>"+filename+" because "+reason+"</li>"
            message += "</ul>"
        return (True, message)
#    except :
        return False

class iTunesSyncer(object) :
    def __init__(self, xmlparser, library) :
        xmlparser.StartElementHandler = lambda name, attr : self.StartElementHandler(name, attr)
        xmlparser.EndElementHandler = lambda name : self.EndElementHandler(name)
        xmlparser.CharacterDataHandler = lambda data : self.CharacterDataHandler(data)
        self.currentdict = None
        self.currentkey = None
        self.currentmode = None
        self.level = 0 # only start when level=2
        self.lib = library
        self.skippedSongs = []
    def StartElementHandler(self, name, attr) :
        if name == "dict" :
            if self.level < 2 :
                self.level += 1
            else :
                self.currentdict = dict()
                self.level = 3
        elif name == "key" :
            if self.level == 3 :
                self.currentmode = "key"
                self.currentkey = ""
    def CharacterDataHandler(self, data) :
        if self.level == 3 :
            if self.currentmode == "key" :
                self.currentkey += data
            elif self.currentmode == "data" :
                d = self.currentdict
                if self.currentkey == u'Playlist Items' :
                    raise DoneException()
                self.currentdict[self.currentkey] += data
    def EndElementHandler(self, name) :
        if self.level == 2 :
            if name == "array" :
                raise DoneException()
        if self.level == 3 :
            if name == "key" :
                self.currentmode = "data"
                self.currentdict[self.currentkey] = ""
            elif name == "dict" :
                self.level = 2
                if not self.currentdict.has_key("Album") :
                    self.currentdict["Album"] = "*Unknown Album*"
                if not self.currentdict.has_key("Artist") :
                    self.currentdict["Artist"] = "*Unknown Artist*"
                albums = Album.objects.filter(album_library__id = self.lib.id, album_name = self.currentdict["Album"])
                album = None
                if len(albums) == 0 :
                    album = Album(album_library = self.lib,
                                  album_name = self.currentdict["Album"],
                                  album_synchronized = True)
                    album.save()
                else :
                    album = albums[0]
                    album.album_synchronized = True
                    album.save()
                songs = Song.objects.filter(song_filename = self.currentdict["Location"]) # assuming filename is a good enough primary key
                song = None
                d = self.currentdict
                try :
                    modified = iso8601.parse_datetime(d.get("Date Modified", None))
                except :
                    modified = None
                if (not skipiTunesKind(d["Kind"])) and (modified is not None) :
                    if len(songs) == 0 :
                        song = Song(song_name = d.get("Name", None),
                                    song_grouping = d.get("Grouping", None),
                                    song_composer = d.get("Composer", None),
                                    song_artist = d.get("Artist", None),
                                    song_album = album,
                                    song_genre = d.get("Genre", None),
                                    song_time = d.get("Total Time", None),
                                    song_tracknum = d.get("Track Number", None),
                                    song_numbertracks = d.get("Track Count", None),
                                    song_discnum = d.get("Disc Number", None),
                                    song_numberdiscs = d.get("Disc Count", None),
                                    song_filetype = iTunesKindToMime(d["Kind"]),
                                    song_filesize = d.get("Size", None),
                                    song_bitrate = d.get("Bit Rate", None),
                                    song_filename = d.get("Location", None),
                                    song_synchronized = True,
                                    song_modified = modified)
                        song.save()
                    elif songs[0].song_modified < modified :
                        songs.update(song_name = d.get("Name", None),
                                     song_grouping = d.get("Grouping", None),
                                     song_composer = d.get("Composer", None),
                                     song_artist = d.get("Artist", None),
                                     song_album = album,
                                     song_genre = d.get("Genre", None),
                                     song_time = d.get("Total Time", None),
                                     song_tracknum = d.get("Track Number", None),
                                     song_numbertracks = d.get("Track Count", None),
                                     song_discnum = d.get("Disc Number", None),
                                     song_numberdiscs = d.get("Disc Count", None),
                                     song_filetype = iTunesKindToMime(d["Kind"]),
                                     song_filesize = d.get("Size", None),
                                     song_bitrate = d.get("Bit Rate", None),
                                     song_filename = d.get("Location", None),
                                     song_synchronized = True,
                                     song_modified = modified)
                    else :
                        songs.update(song_synchronized = True)
                else :
                    if modified is None :
                        self.skippedSongs.append((d.get("Location"), "Bad last modified string"))
                    else :
                        self.skippedSongs.append((d.get("Location"), "Type \""+d["Kind"]+"\" is unsupported"))
            else :
                self.currentmode = None

iTunesKindsDict = {"AAC audio file" : "audio/mp4",
                   "AIFF audio file" : "audio/x-aiff",
                   "Apple Lossless audio file" : "audio/mp4a",
                   "MPEG audio file" : "audio/mpeg",
                   "MPEG audio stream" : "audio/x-mpegurl",
                   "MPEG-4 video file" : "video/mp4",
                   "WAV audio file" : "audio/x-wav"}

iTunesSkipKinds = {"Protected AAC audio file" : True,
                   "QuickTime movie file" : True,
                   "Protected MPEG-4 video file" : True,
                   "Purchased AAC audio file" : True}

def iTunesKindToMime(kind) :
    return iTunesKindsDict[kind]

def skipiTunesKind(kind) :
    return iTunesSkipKinds.get(kind, False)

##########

def doDirectorySync(lib) :
    if not os.path.exists(lib.library_location) :
        return (False, "No such directory "+lib.library_location)

    Song.objects.filter(song_album__album_library__id = lib.id).update(song_synchronized = False)
    Album.objects.filter(album_library__id = lib.id).update(album_synchronized = False)

    numadded = 0
    numupdated = 0
    numunchanged = 0
    numskipped = 0
    numremoved = 0
    
    message = ""
    for root, dirs, files in os.walk(lib.library_location) :
        for file in files :
            filename = os.path.join(root, file)
            modified = datetime.fromtimestamp(os.path.getmtime(filename))
            songs = Song.objects.filter(song_filename=filename)
            if len(songs) == 0 or songs[0].song_modified < modified : # need to add or update, respectively
                info = None
                try :
                    info = mutagen.File(filename, easy=True)
                except :
                    message += "<p>Bad song file.</p>"
                if info is not None :
                    #message += "<pre>--"+filename+"\n-"+info.pprint()+"</pre>"

                    name = info.get("title", [file])[0]
                    grouping = info.get("grouping", [None])[0]
                    composer = info.get("composer", [None])[0]
                    artist = info.get("artist", [None])[0]
                    albumname = info.get("album", [None])[0]
                    try :
                        genre = info.get("genre", [None])[0]
                    except :
                        genre = None
                    time = int(info.info.length*1000) # sec -> msec
                    tracknum = info.get("tracknumber", [None])[0]
                    numbertracks = None
                    if tracknum != None and len(tracknum.split("/")) > 1 :
                        tracknum, numbertracks = tracknum.split("/")
                    if tracknum != None :
                        try :
                            tracknum = int(tracknum)
                        except ValueError :
                            tracknum = None
                            numbertracks = None
                    if numbertracks != None :
                        try :
                            numbertracks = int(numbertracks)
                        except ValueError :
                            numbertracks = None
                    discnum = info.get("discnumber", [None])[0]
                    numberdiscs = None
                    if discnum != None and len(discnum.split("/")) > 1 :
                        discnum, numberdiscs = discnum.split("/")
                    if discnum != None :
                        try :
                            discnum = int(discnum)
                        except ValueError :
                            discnum = None
                            numberdiscs = None
                    if numberdiscs != None :
                        try :
                            numberdiscs = int(numberdiscs)
                        except ValueError :
                            numberdiscs = None
                    filetype = info.mime[0] # just take first one?
                    filesize = os.path.getsize(filename)
                    try :
                        bitrate = int(info.info.bitrate/1000) # bps -> kbps
                    except AttributeError :
                        bitrate = None # flac
                    
                    if albumname == None :
                        head, tail = os.path.split(root)
                        if tail == "" or len(head) < len(lib.library_location) :
                            albumname = "*Unknown Album*"
                        else :
                            albumname = tail
                    if artist == None :
                        artist = "*Unknown Artist*"

                    albums = Album.objects.filter(album_library__id = lib.id, album_name = albumname)
                    album = None
                    if len(albums) == 0 :
                        album = Album(album_library = lib,
                                      album_name = albumname,
                                      album_synchronized = True)
                        album.save()
                    else :
                        album = albums[0]
                        album.album_synchronized = True
                        album.save()
                    
                    if len(songs) == 0 :
                        numadded += 1
                        song = Song(song_name = name,
                                    song_grouping = grouping,
                                    song_composer = composer,
                                    song_artist = artist,
                                    song_album = album,
                                    song_genre = genre,
                                    song_time = time,
                                    song_tracknum = tracknum,
                                    song_numbertracks = numbertracks,
                                    song_discnum = discnum,
                                    song_numberdiscs = numberdiscs,
                                    song_filetype = filetype,
                                    song_filesize = filesize,
                                    song_bitrate = bitrate,
                                    song_filename = filename,
                                    song_synchronized = True,
                                    song_modified = modified)
                        song.save()
                    else :
                        numupdated += 1
                        songs.update(song_name = name,
                                     song_grouping = grouping,
                                     song_composer = composer,
                                     song_artist = artist,
                                     song_album = album,
                                     song_genre = genre,
                                     song_time = time,
                                     song_tracknum = tracknum,
                                     song_numbertracks = numbertracks,
                                     song_discnum = discnum,
                                     song_numberdiscs = numberdiscs,
                                     song_filetype = filetype,
                                     song_filesize = filesize,
                                     song_bitrate = bitrate,
                                     song_filename = filename,
                                     song_synchronized = True,
                                     song_modified = modified)
                else :
                    numskipped += 1
                    message += "<p>Skipped non-sound file "+filename+"</p>"
            elif len(songs) > 0 : # the file is in the database, just need to update
                songs[0].song_synchronized = True
                songs[0].song_album.album_synchronized = True
                songs[0].save()
                songs[0].song_album.save()
                numunchanged += 1
            else :
                numremoved += 1

    Song.objects.filter(song_album__album_library__id = lib.id, song_synchronized = False).delete()
    Album.objects.filter(album_library__id = lib.id, album_synchronized = False).delete()
    
    lib.last_synchronized = datetime.now()
    lib.save()
    return (True, ("<p>%d added, %d updated, %d unchanged, %d removed, and %d skipped.</p>" % (numadded, numupdated, numunchanged, numremoved, numskipped)) + message)


#######

# right now just drops external library and restarts...
def doExternalSync(lib) :
    try :
        serialized = json.loads(urllib.urlopen(lib.library_location+"/dump/").read())
    except :
        return (False, "Can't access external library \""+lib.library_location+"\"")

    Song.objects.filter(song_album__album_library__id = lib.id).delete()
    Album.objects.filter(album_library__id = lib.id).delete()

    numalbums = 0
    numsongs = 0

    album_mapping = dict()
    for album in serialized["albums"] :
        numalbums += 1
        a = Album(album_library = lib,
                  album_external_id = album["id"],
                  album_name = album["name"],
                  album_synchronized = True)
        a.save()
        album_mapping[album["id"]] = a
    for song in serialized["songs"] :
        numsongs += 1
        s = Song(song_name = song["name"],
                 song_grouping = song["grouping"],
                 song_composer = song["composer"],
                 song_artist = song["artist"],
                 song_album = album_mapping[song["album"]],
                 song_genre = song["genre"],
                 song_time = song["time"],
                 song_tracknum = song["tracknum"],
                 song_numbertracks = song["numbertracks"],
                 song_discnum = song["discnum"],
                 song_numberdiscs = song["numberdiscs"],
                 song_filetype = song["filetype"],
                 song_filesize = song["filesize"],
                 song_bitrate = song["bitrate"],
                 song_filename = song["filename"],
                 song_synchronized = True,
                 song_modified = datetime.fromtimestamp(song["modified"]))
        s.save()
    
    lib.last_synchronized = datetime.now()
    lib.save()
    return (True, "Added %d songs in %d albums." % (numsongs, numalbums))
