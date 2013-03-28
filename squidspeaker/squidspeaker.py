# interface between player, playlist, and network

import playlist
import player
import mplayer
import socket
import SocketServer
import pickle
import threading
from minirpc.rpc import RPCServable, rpcmethod, RPCServer

theSpeakerLock = threading.Lock()

class SquidSpeakerHandler(RPCServable) :

    def __init__(self, player, playlist) :
        self.player = player
        self.playlist = playlist

    def __around_rpc__(self, call) :
        with theSpeakerLock :
            return call()

    def nextSong(self, player) : # callback for player
        self.next()

    @rpcmethod
    def prev(self) :
        song = self.playlist.previousSong()
        if song is not None :
            self.player.play(song["filename"], self.nextSong)
        else :
            self.player.stop()
    @rpcmethod
    def pause(self) :
        self.player.pause()
    @rpcmethod
    def play(self) :
        if self.player.isPlaying() :
            self.player.unpause()
        else :
            song = self.playlist.currentSong()
            if song is None :
                self.playlist.randomize(False)
                song = self.playlist.currentSong()
            if song is not None :
                self.player.play(song["filename"], self.nextSong)
    @rpcmethod
    def stop(self) :
        self.player.stop()
    @rpcmethod
    def next(self) :
        song = self.playlist.nextSong()
        if song is not None :
            self.player.play(song["filename"], self.nextSong)
        else :
            if self.player.isRunning() :
                self.player.stop()
    @rpcmethod
    def add(self, songs) :
        """Adds a list of songs to the playlist."""
        puid = self.playlist.addSongs(songs)
        if not self.player.isPlaying() :
            self.playlist.setSong(puid)
            song = self.playlist.currentSong()
            self.player.play(song["filename"], self.nextSong)
    @rpcmethod
    def insert(self, songs, location) :
        """Inserts a list of songs after a particular index ('location')."""
        self.playlist.insertSongs(songs, location)
    @rpcmethod
    def move(self, puid, index) :
        """puid is song to move, index is new index of song"""
        self.playlist.moveSong(puid, index)
    @rpcmethod
    def queue(self, puid, number) :
        if self.player.isPlaying() and len(self.playlist.queued) == 0 :
            self.playlist.queueSong(self.playlist.currentSong()["puid"], 0)
        self.playlist.queueSong(puid, number)
        if number == 0 and self.player.isPlaying() :
            self.stop()
        if not self.player.isPlaying() :
            self.play()
    @rpcmethod
    def set(self, puid) :
        self.playlist.setSong(puid)
        song = self.playlist.currentSong()
        self.player.play(song["filename"], self.nextSong)
    @rpcmethod
    def shuffle(self, shouldShuffle) :
        """shouldShuffle is a boolean"""
        song = self.playlist.currentSong()
        self.playlist.shuffle = shouldShuffle
        self.playlist.setSong(song["puid"])
        #self.player.play(song["filename"], self.nextSong)
    @rpcmethod
    def loop(self, shouldLoop) :
        """shouldLoop is a boolean"""
        self.playlist.loop = shouldLoop
    @rpcmethod
    def clear(self) :
        self.player.stop()
        self.playlist.deleteSongs([x["puid"] for x in self.playlist.list])
    @rpcmethod
    def clean(self) :
        self.playlist.deleteSongs(self.playlist.previousSongs())
    @rpcmethod
    def delete(self, puids) :
        if self.player.isPlaying() :
            song = self.playlist.currentSong()
            if song["puid"] in puids :
                self.player.stop()
        print "deleting", puids
        self.playlist.deleteSongs(puids)
    @rpcmethod("playlist")
    def get_playlist(self) :
        return {"playlist" : self.playlist.list,
                "queued" : self.playlist.queued,
                "playing" : self.playlist.currentSong(),
                "isPlaying" : self.player.isPlaying(),
                "shuffle" : self.playlist.shuffle,
                "volume" : self.player.getVolume(),
                "position" : self.player.getPosition(),
                "loop" : self.playlist.loop}
    @rpcmethod
    def raiseVolume(self) :
        self.player.raiseVolume()
    @rpcmethod
    def lowerVolume(self) :
        self.player.lowerVolume()
    @rpcmethod
    def getVolume(self) :
        return self.player.getVolume()
    @rpcmethod
    def getPosition(self) :
        return self.player.getPosition()
    @rpcmethod
    def setPosition(self, offset) :
        """offset is float in seconds"""
        self.player.setPosition(offset)

def getPassword() :
    import settings
    return settings.SPEAKER_PASSWORD

thePlayer = mplayer.MplayerDriver()

def getPlayer() :
    return thePlayer

class ReusingTCPServer(SocketServer.TCPServer) :
    allow_reuse_address = True

if __name__ == "__main__" :
    HOST, PORT = "0.0.0.0", 21212

    print "* Squidspeaker server *"
    handler = SquidSpeakerHandler(getPlayer(), playlist.Playlist())
    print "Server loaded."
    RPCServer((HOST, PORT), handler, password=getPassword()).serve_forever()
