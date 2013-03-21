from squidmusic.squidmusicweb.models import MusicLibrary, SquidSpeaker, Album, Song
from django.contrib import admin
from datetime import datetime
from squidmusic.squidmusicweb.library import doLibrarySynchronization, doInferGroupings
from django.http import HttpResponse, Http404

class MusicLibraryAdmin(admin.ModelAdmin) :
    actions = ['synchronize_library', 'infer_groupings']
    list_display = ['library_name', 'last_synchronized']

    def synchronize_library(modeladmin, request, queryset) :
        ret = doLibrarySynchronization(queryset)
        #if ret is not None :
        #    modeladmin.message_user(request, ret)
        response = HttpResponse()
        response.write(ret)
        return response
    synchronize_library.short_description = "Synchronize the library"

    def infer_groupings(modeladmin, request, queryset) :
        ret = ""
        for lib in queryset :
            ret += doInferGroupings(lib)
        response = HttpResponse()
        response.write(ret)
        return response
    infer_groupings.short_description = "Infer grouping tag for songs in library"

admin.site.register(MusicLibrary, MusicLibraryAdmin)
admin.site.register(SquidSpeaker)
admin.site.register(Album)
admin.site.register(Song)
