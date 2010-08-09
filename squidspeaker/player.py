# Player interface
# Anything which is a squidmusic player must use this as an interface

class PlayerInterface(object) :
    def play(self, filename, callback) :
        """Takes a filename to play and a callback function which is
        called when the file is done playing.  The callback function
        is a function which takes the player interface object."""
        raise NotImplementedError("play not implemented")

    def stop(self) :
        """Tells the player to stop the music.  Although the current
        song is stopped, the callback from play should not be
        executed."""
        raise NotImplementedError("stop not implemented")

    def pause(self) :
        """Tells the player to pause the current song."""
        raise NotImplementedError("pause not implemented")

    def unpause(self) :
        """Tells the player to unpause the current song."""
        raise NotImplementedError("unpause not implemented")

    def isPlaying(self) :
        """Returns a boolean for whether a song is playing (even if
        paused."""
        raise NotImplementedError("isPlaying not implemented")

    def raiseVolume(self) :
        """Raises the volume."""
        raise NotImplementedError("raiseVolume not implemented")

    def lowerVolume(self) :
        """Lowers the volume."""
        raise NotImplementedError("lowerVolume not implemented")
