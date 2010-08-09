# playlist object

import random

class Playlist(object) :
    def __init__(self) :
        self.npuid = 0
        self.list = list() # list of dicts, and "filename" is one key
        self.randomized = list() # list of indices of list
        self.shuffle = False # whether to follow randomized list
        self.loop = False # whether to restart the list once completed
        self.queued = list() # list of songs (by puid) to play before other lists
        self.index = 0 # the current song index in self.list to play

    def currentSong(self) :
        """Gets the currently playing song."""
        if len(self.queued) > 0 : # any queued songs?
            puid = self.queued[0] # this is convoluted because it works nice when the queue is emptied
            if self.shuffle :
                self.index = [i for i in range(0, len(self.list)) if self.list[self.randomized[i]]["puid"] == puid][0]
            else :
                self.index = [i for i in range(0, len(self.list)) if self.list[i]["puid"] == puid][0]
            return self.list[self.index]
        elif len(self.list) > 0 and self.index < len(self.list):
            if self.shuffle : # on shuffle mode?
                return self.list[self.randomized[self.index]]
            else :
                return self.list[self.index]
        else : # no songs
            return None

    def getQueued(self) :
        """Gets the currently queued songs."""
        return [[s for s in self.list if s["puid"] == p] for p in self.queued]

    def nextSong(self) :
        """Moves the playlist to the next song.  The return value is
        the same as future calls to currentSong."""
        if len(self.queued) > 0 :
            self.queued = self.queued[1:] # remove first element of queue
            self.index += 1 # for if the queue becomes empty
        elif len(self.list) > 0 and self.index < len(self.list) and (not self.loop or self.index + 1 != len(self.list)) :
            self.index += 1
        elif self.loop :
            self.randomize(False)
        else :
            pass # done with the playlist
        return self.currentSong()

    def previousSong(self) :
        """Moves the playlist to the previous song."""
        self.queued = []
        if len(self.list) > 0 :
            self.index = (self.index - 1) % len(self.list)
        else :
            self.index = 0
        return self.currentSong()

    def setSong(self, puid) :
        """Moves the playlist to a particular song."""
        self.queued = []
        self.randomize(False)
        if self.shuffle :
            self.index = [i for i in range(0, len(self.list)) if self.randomized[i] == puid][0]
        else :
            self.index = [i for i in range(0, len(self.list)) if self.list[i]["puid"] == puid][0]

    def randomize(self, keepCurrentSong = True) :
        """Randomizes the index array for random mode, and sets index
        to 0. If keepCurrentSong is true, and the queue is empty, then
        the currently playing index is brought to index zero of the
        randomized list."""
        if self.index >= len(self.list) :
            self.index = 0
        if len(self.list) == 0 :
            self.randomized = list()
            self.index = 0
        elif len(self.list) == len(self.randomized) :
            currIndex = self.index
            if self.shuffle and self.index < len(self.list) :
                currIndex = self.randomized[self.index]
            self.index = 0
            self.randomized = range(0, len(self.list))
            random.shuffle(self.randomized)
            if keepCurrentSong and len(self.queued) == 0 :
                for i in range(0, len(self.list)) :
                    if self.randomized[i] == currIndex :
                        self.randomized[i] = self.randomized[0]
                        self.randomized[0] = currIndex
                        break
        else :
            self.randomized = range(0, len(self.list))
            random.shuffle(self.randomized)

    def insertSongs(self, songs, index) :
        """Inserts each of songs into the playlist at the given index,
        and each song is given a puid (playlist unique id). The first
        puid is returned."""
        for song in songs :
            song["puid"] = self.npuid
            self.npuid += 1
        self.list = self.list[0:index] + songs + self.list[index:]
        self.randomize()
        return songs[0]["puid"]

    def addSongs(self, songs) :
        """Appends each of the songs to the end of the playlist.
        Puids are also added.  The first puid is returned"""
        for song in songs :
            song["puid"] = self.npuid
            self.npuid += 1
        retpuid = songs[0]["puid"]
        self.list = self.list + songs
        self.randomize()
        return retpuid

    def moveSong(self, puid, index) :
        """Takes song with puid and makes it at index index in the
        playlist."""
        current = self.currentSong()
        songindex = [i for i in range(0, len(self.list)) if self.list[i]["puid"] == puid][0]
#        currentsongindex = None
#        if current is not None :
#            currentsongindex = [i for i in range(0, len(self.list)) if self.list[i] == current][0]
#        print current, songindex, currentsongindex
        print self.list[songindex]
        if songindex == index :
            # already there
            pass
        elif songindex < index :
            self.list = self.list[0:songindex]+self.list[songindex+1:index+1]+[self.list[songindex]]+self.list[index+1:]
            self.randomized = self.randomized[0:songindex]+self.randomized[songindex+1:index+1]+[self.randomized[songindex]]+self.randomized[index+1:]
        elif songindex > index :
            self.list = self.list[0:index] + [self.list[songindex]] + self.list[index:songindex] + self.list[songindex+1:]
            self.randomized = self.randomized[0:index] + [self.randomized[songindex]] + self.randomized[index:songindex] + self.randomized[songindex+1:]
        queued = [x for x in self.queued]
        if current is not None :
            self.setSong(current["puid"])
        if len(queued) > 0 :
            self.queued = queued
            self.currentSong() # updates self.index

    def deleteSongs(self, puids) :
        """Deletes songs from the playlist by puids."""
        curr = self.currentSong()
        self.queued = [x for x in self.queued if x not in puids]
        self.list = [x for x in self.list if x["puid"] not in puids]
        if curr == None or (curr["puid"] not in self.queued and curr["puid"] not in [s["puid"] for s in self.list]):
            self.randomize(False)
        else :
            self.randomize(False)
            if len(self.queued) == 0 :
                id = [i for i in range(0, len(self.list)) if self.list[i]["puid"] == curr["puid"]][0]
                if self.shuffle :
                    for i in range(0, len(self.list)) :
                        if self.randomized[i] == id :
                            self.randomized[i] = self.randomized[0]
                            self.randomized[0] = id
                            self.index = 0
                            break
                else :
                    self.index = id
        if self.index >= len(self.list) :
            self.index = 0

    def queueSong(self, puid, number) :
        """Queues a song to be played after number songs."""
        if number >= len(self.queued) :
            self.queued.append(puid)
        else :
            self.queued = self.queued[0:number] + [puid]

if __name__=="__main__" :
    p = Playlist()
    p.addSongs([{"filename":"a"}, {"filename":"b"}, {"filename":"c"}])
    p.setSong(1)
    p.moveSong(2, 0)
    print p.list
    print p.currentSong()
