# squid speaker client

import socket
import pickle # pickle.dumps(obj)

class SquidSpeakerClient(object) :
    def __init__(self, server, port, password) :
        self.server = server
        self.port = port
        self.password = password

    def send(self, command, data = None) :
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((self.server, self.port))
        d = pickle.dumps(data).encode('base64')
        self.sock.send(self.password + "\n" + command + "\n" + str(len(d)) + "\n" + d)
        f = self.sock.makefile()
        ret = pickle.loads(f.read(int(f.readline())).decode('base64'))
        self.sock.close()
        return ret

    def prev(self) :
        self.send("prev")

    def pause(self) :
        self.send("pause")

    def play(self) :
        self.send("play")

    def stop(self) :
        self.send("stop")

    def next(self) :
        self.send("next")

    def add(self, songs) :
        self.send("add", songs)

    def insert(self, songs, location) :
        self.send("insert", {"songs" : songs, "location" : location})

    def move(self, puid, index) :
        self.send("move", {"puid" : puid, "index" : index})

    def queue(self, puid, number) :
        self.send("queue", {"puid" : puid, "number" : number})

    def set(self, puid) :
        self.send("set", puid)

    def shuffle(self, val) :
        self.send("shuffle", val)

    def loop(self, val) :
        self.send("loop", val)

    def clear(self) :
        self.send("clear")

    def clean(self) :
        self.send("clean")

    def delete(self, puids) :
        self.send("delete", puids)

    def playlist(self) :
        return self.send("playlist")

    def raiseVolume(self) :
        self.send("raiseVolume")

    def lowerVolume(self) :
        self.send("lowerVolume")

    def getVolume(self) :
        return self.send("getVolume")

    def getPosition(self) :
        return self.send("getVolume")

    def setPosition(self, milliseconds) :
        self.send("setPosition", milliseconds)

if __name__ == "__main__" :
    ssc = SquidSpeakerClient("localhost", 21212, "waldo")
    print ssc.playlist()
    ssc.add([{"filename" : "/Users/kyle/Desktop/21m302t_and_v.aiff"}])
    print ssc.playlist()
#    ssc.play()
    #ssc.pause()
    ssc.queue(0,1)
