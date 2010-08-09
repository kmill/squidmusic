# Create your views here.

from django.template import Context, loader, Template
from squidmusicweb.models import MusicLibrary, Album, Song, SquidSpeaker
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core import serializers
import json
from django.shortcuts import render_to_response
from django.db.models import Q
from squidspeaker.squidspeakerclient import SquidSpeakerClient
from urlparse import urlparse
from urllib import urlopen, unquote
from squidmusicweb.templatetags.time_conversion import msec_to_string
from datetime import datetime
import time
from django.core.urlresolvers import reverse
from settings import URL_ROOT_PATH

def index(request) :
    search = request.GET.get("search", "")
    songs_list = Song.objects.all()
    if search != "" :
        searchterms = [x.strip() for x in search.split(" ")]
        for term in searchterms :
            songs_list = songs_list.filter(Q(song_name__icontains=term)
                                           | Q(song_grouping__icontains=term)
                                           | Q(song_composer__icontains=term)
                                           | Q(song_artist__icontains=term)
                                           | Q(song_album__album_name__icontains=term))
    songs_list = songs_list.order_by('song_album__album_name', 'song_album__album_library__id', 'song_discnum', 'song_tracknum')
    paginator = Paginator(songs_list, 100)

    try :
        speaker = SquidSpeaker.objects.filter()[0] # fix this!  need session or something
    except :
        speaker = None

    try :
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try :
        songs = paginator.page(page)
    except (EmptyPage, InvalidPage) :
        songs = paginator.page(paginator.num_pages)

    return render_to_response('list.html', {"songs" : songs, "speaker" : speaker, "search" : search})

def song(request, songid) :
    if request.GET.has_key("download") :
        try :
            songid = int(songid)
            song = Song.objects.filter(id=songid)[0]
            o = urlparse(song.song_filename)
            #        if o.scheme != "file" :
            #            raise Exception("Not on this server")
            sent_filename = unquote(o.path.split("/")[-1])
            f = urlopen(song.song_filename)
            response = HttpResponse(f.read(), mimetype=song.song_filetype)
            response['Content-Disposition'] = 'attachment; filename='+sent_filename.encode("utf-8")
            return response
        except :
            raise Http404
    else :
        songid = int(songid)
        songs = Song.objects.filter(id=songid)
        if len(songs) > 0 :
            return render_to_response('songinfo.html', {"song" : songs[0]})
        else :
            raise Http404

def players(request, message="") :
    setdefault = request.GET.get("setdefault", None)
    if setdefault is not None :
        request.session["playerid"] = int(setdefault)
    players = SquidSpeaker.objects.all()
    playerid = None
    if request.session.has_key("playerid") :
        playerid = int(request.session["playerid"])
    return render_to_response('squidspeakers.html', {"speakers" : players,
                                                     "message" : message,
                                                     "playerid" : playerid})

def playlist(request, playerid = None) :
    if playerid == None :
        playerid = request.session.get("playerid", None)
        if playerid == None :
            return players(request, "<p>You haven't set a default player.  Please set one first.</p>")
    command = request.GET.get("command", None)
    speaker = SquidSpeaker.objects.filter(id=playerid)[0]
    ssc = SquidSpeakerClient(speaker.speaker_server, speaker.speaker_port, speaker.speaker_password)

    if command == "prev" :
        ssc.prev()
    elif command == "pause" :
        ssc.pause()
    elif command == "play" :
        ssc.play()
    elif command == "stop" :
        ssc.stop()
    elif command == "next" :
        ssc.next()
    elif command == "queue" :
        try :
            puid = int(request.GET.get("puid", None))
            number = int(request.GET.get("number", None))
            ssc.queue(puid, number)
        except :
            pass
    elif command == "set" :
        try :
            puid = int(request.GET.get("puid", None))
            ssc.set(puid)
        except :
            pass
    elif command == "loop" :
        state = request.GET.get("value", False) == "True"
        ssc.loop(state)
    elif command == "shuffle" :
        state = request.GET.get("value", False) == "True"
        ssc.shuffle(state)
    elif command == "clear" :
        ssc.clear()
    elif command == "add" :
        songid = request.GET["id"]
        song = Song.objects.filter(id=songid)[0]
#        t = Template("{% url squidmusicweb.views.song songid=song.id %}")
#        url = t.render(Context({"song" : song}))
        # use django.core.urlresolvers.reverse?
        #url = "http://kmill.mit.edu:8000/song/" + str(song.id)
        url = URL_ROOT_PATH+reverse('squidmusicweb.views.song', kwargs={"songid": song.id})
        s = song.toDict()
        s["filename"] = url+"?download"
        s["infolink"] = url
        ssc.add([s])
    elif command == "addalbum" :
        albumid = request.GET["id"]
        songs = Song.objects.filter(song_album__id=albumid).order_by('song_album__album_name',
                                                                     'song_discnum',
                                                                     'song_tracknum')
#        t = Template("{% url squidmusicweb.views.song songid=song.id %}")
        ss = []
        for song in songs :
 #           url = t.render(Context({"song" : song}))
            url = URL_ROOT_PATH+reverse('squidmusicweb.views.song', kwargs={"songid": song.id})
            s = song.toDict()
            s["filename"] = url+"?download"
            s["infolink"] = url
            ss.append(s)
        ssc.add(ss)
    elif command == "addgroup" :
        albumid = request.GET["albumid"]
        grouping = request.GET["group"]
        songs = Song.objects.filter(song_album__id=albumid, song_grouping=grouping).order_by('song_album__album_name',
                                                                                             'song_discnum',
                                                                                             'song_tracknum')
#        t = Template("{% url squidmusicweb.views.song songid=song.id %}")
        ss = []
        for song in songs :
 #           url = t.render(Context({"song" : song}))
            url = URL_ROOT_PATH+reverse('squidmusicweb.views.song', kwargs={"songid": song.id})
            s = song.toDict()
            s["filename"] = url+"?download"
            s["infolink"] = url
            ss.append(s)
        ssc.add(ss)
    elif command == "movesong" :
        puid = int(request.GET["puid"])
        index = int(request.GET["index"])
        ssc.move(puid, index)
    elif command == "delete" :
        songid = int(request.GET["puid"])
        ssc.delete([songid])
    elif command == "raiseVolume" :
        ssc.raiseVolume()
    elif command == "lowerVolume" :
        ssc.lowerVolume()
    elif command == "seek" :
        seconds = float(request.GET["time"])
        ssc.setPosition(seconds);

    if request.is_ajax() and command != "playlist" and command != None :
        return HttpResponse("done.")
    else :
        playlist = ssc.playlist()
        
        if playlist["volume"] != None :
            try :
                playlist["volume"] = int(float(playlist["volume"]))
            except :
                playlist["volume"] = False
        else :
            playlist["volume"] = False
        if playlist["isPlaying"] :
            playlist["msecsonglength"] = playlist["playing"]["time"]
            try :
                playlist["msecsonglocation"] = int(float(playlist["position"])*1000)
            except :
                playlist["msecsonglocation"] = 0
        
        for song in playlist["playlist"] :
            i = 0
            song["isqueued"] = False
            for q in playlist["queued"] :
                if song["puid"] == q :
                    song["queued"] = i
                    song["isqueued"] = True
                    break
                i += 1
        if request.is_ajax() or command == "playlist" :
            playlist["speakerid"] = speaker.id
            return HttpResponse(json.dumps(playlist), "application/javascript")
        elif command == "m3u" :
#            resp = "#EXTM3U\n"
            resp = ""
            for song in playlist["playlist"] :
#                resp += "#EXTINF:"+str(int(song["time"])//1000)+","+song["artist"]+","+song["name"]+" ("+song["album"]+")\n"
                resp += song["filename"] + "\n"
            return HttpResponse(resp)
        else :
            try :
                playlist["formattedPosition"] = msec_to_string(int(float(playlist["position"])*1000))
                playlist["formattedPositionLeft"] = msec_to_string(int(playlist["playing"]["time"])-int(float(playlist["position"])*1000))
            except :
                # position wasn't formattable.  oops.
                playlist["formattedPosition"] = "Unknown"
                playlist["formattedPositionLeft"] = "Unknown"
            playlist["speaker"] = speaker
            return render_to_response("player_control.html", playlist)

def player_song_row(request) :
    k = dict()
    for key,value in request.POST.items() :
        if value == "null" :
            k[key] = None
        else :
            k[key] = value
        if key == "isqueued" :
            k[key] = (value == "true")
    s = {"id" : request.POST["speakerid"][0]}
    return render_to_response("player_song_row.html", {"song" : k, "speaker" : s})

def library_serialize(request) :
    datefilter = request.GET.get("modified", None)

    s_albums = []
    s_songs = []

    for library in MusicLibrary.objects.exclude(library_type="external") : # don't want to pass on external media because of complications
        for album in Album.objects.filter(album_library = library) :
            songs = Song.objects.filter(song_album=album)
            if datefilter is not None :
                songs = songs.filter(song_modified__gt=datetime.fromtimestamp(float(datefilter)))
            if len(songs) > 0 :
                a = {"id" : album.id, "name" : album.album_name }
                s_albums.append(a)
            for song in songs :
                s = {"filename" : URL_ROOT_PATH+reverse('song', kwargs={"squidmusicweb.views.songid": song.id})+"?download",
                     "name" : song.song_name,
                     "grouping" : song.song_grouping,
                     "composer" : song.song_composer,
                     "artist" : song.song_artist,
                     "album" : album.id,
                     "genre" : song.song_genre,
                     "tracknum" : song.song_tracknum,
                     "numbertracks" : song.song_numbertracks,
                     "discnum" : song.song_discnum,
                     "numberdiscs" : song.song_numberdiscs,
                     "filetype" : song.song_filetype,
                     "filesize" : song.song_filesize,
                     "bitrate" : song.song_bitrate,
                     "time" : song.song_time,
                     "modified" : time.mktime(song.song_modified.timetuple())}
                s_songs.append(s)

    serialized = {"albums" : s_albums, "songs" : s_songs}
    return HttpResponse(json.dumps(serialized), mimetype="application/json")
