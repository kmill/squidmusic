from django.db import models

# Create your models here.

class MusicLibrary(models.Model) :
    LIBRARY_TYPE_CHOICES = (
        (u'iTunes', u'local iTunes music library'),
        (u'directory', u'local directory'),
        (u'external', u'squidmusic server'))

    library_name = models.CharField(max_length=60, unique=True)
    library_type = models.CharField(max_length=20, choices=LIBRARY_TYPE_CHOICES)
    library_location = models.CharField(max_length=256)
    last_synchronized = models.DateTimeField(null=True, blank=True)

    def __unicode__(self) :
        return self.library_name

    class Meta :
        verbose_name_plural = "music libraries"

class Album(models.Model) :
    album_library = models.ForeignKey(MusicLibrary)
    album_external_id = models.IntegerField(null=True, blank=True) # for when the library is "external"
    album_name = models.CharField(max_length=256)
    album_synchronized = models.BooleanField() # used to remove stale album records

    def __unicode__(self) :
        return self.album_name

    class Meta :
        ordering = ['album_name']

class Song(models.Model) :
    song_name = models.CharField(max_length=256)
    song_grouping = models.CharField(max_length=256, null=True, blank=True)
    song_composer = models.CharField(max_length=256, null=True, blank=True)
    song_artist = models.CharField(max_length=256, null=True, blank=True)
    song_album = models.ForeignKey(Album)
    song_genre = models.CharField(max_length=64, null=True, blank=True)
    song_tracknum = models.IntegerField(null=True, blank=True)
    song_numbertracks = models.IntegerField(null=True, blank=True)
    song_discnum = models.IntegerField(null=True, blank=True)
    song_numberdiscs = models.IntegerField(null=True, blank=True)
    song_filetype = models.CharField(max_length=64)
    song_filesize = models.IntegerField()
    song_bitrate = models.IntegerField(null=True, blank=True) # lossless codecs
    song_time = models.IntegerField()
    song_filename = models.CharField(max_length=512)
    song_modified = models.DateTimeField()
    song_synchronized = models.BooleanField() # used to remove stale song records

    def __unicode__(self) :
        return self.song_name + "; " + self.song_album.album_name

    def toDict(self) :
        return {"filename" : self.song_filename,
                "name" : self.song_name,
                "grouping" : self.song_grouping,
                "composer" : self.song_composer,
                "artist" : self.song_artist,
                "album" : self.song_album.album_name,
                "genre" : self.song_genre,
                "tracknum" : self.song_tracknum,
                "numbertracks" : self.song_numbertracks,
                "discnum" : self.song_discnum,
                "numberdiscs" : self.song_numberdiscs,
                "filetype" : self.song_filetype,
                "filesize" : self.song_filesize,
                "bitrate" : self.song_bitrate,
                "time" : self.song_time,
#                "modified" : self.song_modified # not json-able.  just ignoring, clients don't really need this field anyway
                }


    class Meta :
        order_with_respect_to = 'song_album'
        ordering = ['song_tracknum','song_grouping']

class SquidSpeaker(models.Model) :
    speaker_server = models.CharField(max_length=128)
    speaker_port = models.IntegerField()
    speaker_password = models.CharField(max_length=256)

    def __unicode__(self) :
        return self.speaker_server
