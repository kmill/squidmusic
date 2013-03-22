from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^squidmusic/', include('squidmusic.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^m/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^favicon.ico', 'django.views.generic.simple.redirect_to', {'url': '/m/images/favicon.ico'}),
    (r'^$', 'django.views.generic.simple.redirect_to', {'url' : '/music/'}),
    (r'^music/$', 'squidmusicweb.views.index'),
    (r'^dump/$', 'squidmusicweb.views.library_serialize'),
    (r'^players/$', 'squidmusicweb.views.players'),
    (r'^playlists/$', 'squidmusicweb.views.playlist'),
    (r'^playlists/(?P<playerid>\d+)$', 'squidmusicweb.views.playlist'),
    (r'^song/(?P<songid>\d+)$', 'squidmusicweb.views.song'),
    (r'^render/player_song_row$', 'squidmusicweb.views.player_song_row'),
)
