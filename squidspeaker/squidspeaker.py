# interface between player, playlist, and network

import playlist
import player
import mplayer
import socket
import SocketServer
import pickle
import threading

thePlaylist = playlist.Playlist()

theSpeakerLock = threading.Lock()

class SquidSpeakerHandler(SocketServer.BaseRequestHandler) :

    def setup(self) :
        self.player = getPlayer()
        self.password = getPassword()
        self.playlist = thePlaylist

    def handle(self) :
        try :
            self.rfile = self.request.makefile()
            if self.password != self.rfile.readline()[:-1] :
                print "invalid password"
                return
            command = self.rfile.readline()[:-1]
            length = int(self.rfile.readline())
#            print command, length
            r = self.rfile.read(length).decode('base64')
#            print "r:",r
            data = pickle.loads(r)
#            print data
            theSpeakerLock.acquire()
            resp = self.handleCommand(command, data)
            rd = pickle.dumps(resp).encode('base64')
            self.request.send(str(len(rd))+"\n")
            self.request.send(rd)
        except Exception :
            print "Exception! Ignoring" #,type(x), x.args, x
#            raise
        theSpeakerLock.release()

    def nextSong(self, player) : # callback for player
        self.handleCommand("next")

    def handleCommand(self, command, data=None) :
        print "handling", command
        if command == "prev" :
            song = self.playlist.previousSong()
            if song is not None :
                self.player.play(song["filename"], self.nextSong)
            else :
                self.player.stop()
        elif command == "pause" :
            self.player.pause()
        elif command == "play" :
            if self.player.isPlaying() :
                self.player.unpause()
            else :
                song = self.playlist.currentSong()
                if song is None :
                    self.playlist.randomize(False)
                    song = self.playlist.currentSong()
                if song is not None :
                    self.player.play(song["filename"], self.nextSong)
        elif command == "stop" :
            self.player.stop()
        elif command == "next" :
            song = self.playlist.nextSong()
            if song is not None :
                self.player.play(song["filename"], self.nextSong)
            else :
                if self.player.isRunning() :
                    self.player.stop()
        elif command == "add" : # data is list of songs
            puid = self.playlist.addSongs(data)
            if not self.player.isPlaying() :
                self.playlist.setSong(puid)
                song = self.playlist.currentSong()
                self.player.play(song["filename"], self.nextSong)
        elif command == "insert" : # data["songs"] is list of songs, data["location"] is index to insert
            self.playlist.insertSongs(data["songs"], data["location"])
        elif command == "move" : # data["puid"] is song to move, data["index"] is new index of song
            self.playlist.moveSong(data["puid"], data["index"])
        elif command == "queue" :
            if self.player.isPlaying() and len(self.playlist.queued) == 0 :
                self.playlist.queueSong(self.playlist.currentSong()["puid"], 0)
            self.playlist.queueSong(data["puid"], data["number"])
            if data["number"] == 0 and self.player.isPlaying() :
                self.handleCommand("stop")
            if not self.player.isPlaying() :
                self.handleCommand("play")
        elif command == "set" : # data is puid
            self.playlist.setSong(data)
            song = self.playlist.currentSong()
            self.player.play(song["filename"], self.nextSong)
        elif command == "shuffle" : # data is boolean
            song = self.playlist.currentSong()
            self.playlist.shuffle = data
            self.playlist.setSong(song["puid"])
#            self.player.play(song["filename"], self.nextSong)
        elif command == "loop" : # data is boolean
            self.playlist.loop = data
        elif command == "clear" :
            self.player.stop()
            self.playlist.deleteSongs([x["puid"] for x in self.playlist.list])
        elif command == "clean" :
            self.playlist.deleteSongs(self.playlist.previousSongs())
        elif command == "delete" :
            if self.player.isPlaying() :
                song = self.playlist.currentSong()
                if song["puid"] in data :
                    self.player.stop()
            print "deleting", data
            self.playlist.deleteSongs(data)
        elif command == "playlist" :
            return {"playlist" : self.playlist.list,
                    "queued" : self.playlist.queued,
                    "playing" : self.playlist.currentSong(),
                    "isPlaying" : self.player.isPlaying(),
                    "shuffle" : self.playlist.shuffle,
                    "volume" : self.player.getVolume(),
                    "position" : self.player.getPosition(),
                    "loop" : self.playlist.loop}
        elif command == "raiseVolume" :
            self.player.raiseVolume()
        elif command == "lowerVolume" :
            self.player.lowerVolume()
        elif command == "getVolume" :
            return self.player.getVolume()
        elif command == "getPosition" :
            return self.player.getPosition()
        elif command == "setPosition" : # data is float in seconds
            self.player.setPosition(data)

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

    server = ReusingTCPServer((HOST, PORT), SquidSpeakerHandler)
    
    print "* Squidspeaker server *"
    print "Server loaded."
    server.serve_forever()
