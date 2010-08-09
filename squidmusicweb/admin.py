from squidmusic.squidmusicweb.models import MusicLibrary, SquidSpeaker, Album, Song
from django.contrib import admin
from datetime import datetime
from squidmusic.squidmusicweb.library import doLibrarySynchronization
from django.http import HttpResponse, Http404

class MusicLibraryAdmin(admin.ModelAdmin) :
    actions = ['synchronize_library']
    list_display = ['library_name', 'last_synchronized']

    def synchronize_library(modeladmin, request, queryset) :
        ret = doLibrarySynchronization(queryset)
        #if ret is not None :
        #    modeladmin.message_user(request, ret)
        response = HttpResponse()
        response.write(ret)
        return response
    synchronize_library.short_description = "Synchronize the library"

admin.site.register(MusicLibrary, MusicLibraryAdmin)
admin.site.register(SquidSpeaker)
admin.site.register(Album)
admin.site.register(Song)
