# mplayer driver

import subprocess
import threading
import player
import time
from urllib import urlretrieve
import os
import tempfile

MPLAYER = "mplayer"
MPLAYER = "/Applications/MPlayer OSX Extended.app/Contents/Resources/Binaries/mpextended.mpBinaries/Contents/mpextended.mpBinaries/Contents/MacOS/mplayer"

class MplayerDriver(player.PlayerInterface) :
    def __init__(self) :
        self.mplayerProcess = None
        self.callback = None
        self.id = 0
        self.mplayerlock = threading.Lock()
        self.lastread = ""
        self.lineno = 0
        self.readProperties = dict()
    def __del__(self) :
        print "Killing mplayer object"
        if self.isRunning() :
            self.callback = None
            self.mplayerProcess.terminate()
    def startThread(self, file, callback) :
        keepgoing = self.mplayerlock.acquire(False)
        if not keepgoing :
            print "ERROR: Couldn't get lock to start thread"
            return False
        try :
            print "starting thread"
            self.callback = callback
            def runInThread() :
                print "starting",MPLAYER
                self.mplayerProcess = subprocess.Popen([MPLAYER, "-quiet", "-slave", "-nolirc", file],
                                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                r = self.mplayerProcess.stdout.readline()
                while r != "" :
                    print "got message from mplayer:",r
                    self.lastread = r[:-1] # strip off newline
                    self.lineno += 1
                    try :
                        exp = self.lastread.partition("=")
                        self.readProperties[exp[0][4:]] = exp[2]
                    except :
                        print "message wasn't a property"
                    r = self.mplayerProcess.stdout.readline()
                self.mplayerlock.release() # done with lock on process!
                if self.callback is not None :
                    self.callback(self)
            thread = threading.Thread(target=runInThread, args=())
            thread.start()
            time.sleep(0.1)
        except Exception :
            print "mplayer thread start exception!"
            self.mplayerlock.release()
            pass
        return
    def isRunning(self) :
        if self.mplayerProcess is None :
            return False
        elif self.mplayerProcess.poll() is None :
            return True
        else :
            return False
    def sendCommand(self, commandString) :
        if self.isRunning() :
            self.mplayerProcess.stdin.write(commandString+"\n")
    def getProperty(self, property, keepPausing = True) :
        if self.isRunning() :
            print "getting property:",property
            last = self.lineno
            command = "get_property "+property+"\n"
            if keepPausing :
                command = "pausing_keep_force "+command
            self.mplayerProcess.stdin.write(command)
            while self.lineno == last :
                pass
            print "got property",property,"=",self.readProperties.get(property,None) # may not be accurate--wait until next loop!
            return self.readProperties.get(property,None)
        else :
            return None
    def play(self, songfile, callback) :
        print "mplayer playing",songfile
        isongfile = os.path.join(tempfile.gettempdir(), "mplayer_"+str(os.getpid())+"_"+str(self.id))
        self.id = (self.id+1) % 5
        urlretrieve(songfile, isongfile)
        if self.isRunning() :
            print "playing by sending loadfile"
            self.sendCommand("loadfile "+isongfile)
            self.callback = callback
        else :
            print "playing by starting new thread"
            self.startThread(isongfile, callback)
            
    def stop(self) :
        self.callback = None
        print "stopping"
        self.sendCommand("quit")
        time.sleep(0.1)
    def pause(self) :
        self.getProperty("pause", False) # for some reason get_property unpauses
        self.sendCommand("pause")
    def unpause(self) :
        self.getProperty("pause", False)
    def isPlaying(self) :
        return self.isRunning()
    def raiseVolume(self) :
        self.sendCommand("volume 5")
    def lowerVolume(self) :
        self.sendCommand("volume -5")
    def getVolume(self) :
        return self.getProperty("volume")
    def getPosition(self) :
        return self.getProperty("time_pos") # in seconds
    def setPosition(self, position) : # in seconds
        try :
            self.sendCommand("pausing_keep_force seek "+str(float(position))+" 2")
        except :
            pass
