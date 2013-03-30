# squid speaker client

import socket
import pickle # pickle.dumps(obj)
from minirpc.rpc import RPCClient

class SquidSpeakerClient(RPCClient) :
    def __init__(self, server, port, password) :
        RPCClient.__init__(self, server, port, password=password)

if __name__ == "__main__" :
    ssc = SquidSpeakerClient("localhost", 21212, "waldo")
    print ssc.playlist()
    ssc.add([{"filename" : "/other/music/km/mst.m4a"}])
    print ssc.playlist()
#    ssc.play()
    #ssc.pause()
    ssc.queue(0,1)
