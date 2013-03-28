# rpc.py
# a simple rpc interface

import SocketServer
import socket
import json
import struct
import time
import types

def rpcmethod(name=None) :
    def _rpcmethod(f) :
        f.is_rpc = True
        f.rpc_name = name if type(name) == str else f.func_name
        return f
    if type(name) is types.FunctionType :
        return _rpcmethod(name)
    else :
        return _rpcmethod

class RPCServerMetaclass(type) :
    def __new__(cls, name, bases, dct) :
        dct2 = dct.copy()
        dct2['__rpc__'] = dict((getattr(v, "rpc_name", k), v)
                               for k, v in dct.iteritems() if getattr(v, "is_rpc", False))
        return super(RPCServerMetaclass, cls).__new__(cls, name, bases, dct2)

class RPCServable(object) :
    __metaclass__ = RPCServerMetaclass

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer) :
    allow_reuse_address = True
    daemon_threads = True # for ctrl-c to kill spawned threads

class RPCServer(ThreadedTCPServer) :
    def __init__(self, conninfo, rpcServable, password=None) :
        ThreadedTCPServer.__init__(self, conninfo, self.make_handler(rpcServable, password))
    @staticmethod
    def make_handler(rpcServable, password) :
        if not isinstance(rpcServable, RPCServable) :
            raise Exception("The object must be an instance of RPCServable")
        print "Making rpc server with methods =", rpcServable.__rpc__.keys()
        class RPCHandler(SocketServer.StreamRequestHandler) :
            base_object = rpcServable
            def handle(self) :
                self.request.settimeout(5)
                ident = None
                method = None
                args = None
                kwargs = None
                try :
                    message = self.read_json()
                    if password and password != message["password"] :
                        raise Exception("Incorrect password")
                    if "info" in message :
                        if "dir" == message["info"] :
                            result = sorted(self.base_object.__rpc__.keys())
                        elif "func_doc" == message["info"] :
                            result = self.base_object.__rpc__[message["method"]].func_doc
                        else :
                            raise NotImplementedError("No such info request", message["info"])
                    else :
                        ident = message.get("id", None)
                        method = message.get("method", None)
                        args = message.get("args", [])
                        kwargs = message.get("kwargs", {})
                        print "Handling", self.report_method(method, args, kwargs),
                        print "id=%r" % ident if ident else ""
                        caller = getattr(self.base_object, "__around_rpc__", lambda f : f())
                        forResult = lambda : self.base_object.__rpc__[method](self.base_object, *args, **kwargs)
                        result = caller(forResult)
                    self.write_result(ident, result)
                except Exception as x :
                    print "Exception %r" % x
                    self.write_exception(ident, x)
            def read_json(self) :
                size = struct.unpack("<I", self.request.recv(4))
                data = self.request.recv(size[0])
                return json.loads(data)
            def write_json(self, o) :
                ostring = json.dumps(o)
                self.request.sendall(struct.pack("<I", len(ostring)))
                self.request.sendall(ostring)
            def write_result(self, ident, result) :
                msg = {"id" : ident,
                       "result" : result}
                self.write_json(msg)
            def write_exception(self, ident, exception) :
                msg = {"id" : ident,
                       "error" : {"type" : exception.__class__.__name__,
                                  "args" : exception.args}}
                self.write_json(msg)
            def report_method(self, method, args, kwargs) :
                return "%s(%s)" % (method, ", ".join([repr(a) for a in args]
                                                     + ["%s=%r" % (k, v)
                                                        for k, v in kwargs.iteritems()]))
        return RPCHandler

class RPCException(Exception) :
    pass

class RPCClient(object) :
    def __init__(self, ip, port, password=None) :
        self.__data__ = (ip, port, password)
    def __send_request__(self, msg) :
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip, port, password = self.__data__
        if password :
            msg["password"] = password
        sock.settimeout(222)
        try :
            sock.connect((ip, port))
            ostring = json.dumps(msg)
            sock.sendall(struct.pack("<I", len(ostring)))
            sock.sendall(ostring)
            
            size = struct.unpack("<I", sock.recv(4))
            data = sock.recv(size[0])
            return json.loads(data)
        finally:
            sock.close()
    def __process_request__(self, msg) :
        res = self.__send_request__(msg)
        if "result" in res :
            return res["result"]
        elif "error" in res :
            error = res["error"]
            raise RPCException(error.get("type", "unknown"), error.get("args", []))
        else :
            raise RPCException("Malformed result")
    def __dir__(self) :
        msg = {"info" : "dir"}
        return self.__process_request__(msg)
    def __getattr__(self, name) :
        if name.startswith("__") :
            raise AttributeError("'RPCClient' object has no attribute %r" % name)
        else :
            return RPCFunction(self, name)

class RPCFunction(object) :
    def __init__(self, client, funcname) :
        self.client = client
        self.funcname = funcname
    def __call__(self, *args, **kwargs) :
        msg = {"method" : self.funcname,
               "args" : args,
               "kwargs" : kwargs}
        return self.client.__process_request__(msg)
    @property
    def __name__(self) :
        return self.funcname
    @property
    def func_doc(self) :
        msg = {"info" : "func_doc",
               "method" : self.funcname}
        return self.client.__process_request__(msg)

if __name__ == "__main__" :
    HOST, PORT = "localhost", 22322

    class Test(RPCServable) :
        def __around_rpc__(self, call) :
            print "entered __around_rpc__"
            res = call()
            print "result =", res
            print "leaving __around_rpc__"
            return res
        @rpcmethod
        def hello(self) :
            """Prints 'Hello, World!'"""
            return "Hello, world!"
        @rpcmethod
        def add(self, x, y) :
            """Adds two numbers together"""
            return x + y
        @rpcmethod("test")
        def test_function(self, x) :
            """Tests renaming a function in the rpc interface"""
            return [x, x]
        @rpcmethod
        def exception(self, x) :
            """Throws a KeyError. Always."""
            raise KeyError(x)
        @rpcmethod
        def getargs(self, *args, **kwargs) :
            """Just returns the given arguments."""
            return {"args" : args, "kwargs" : kwargs}

    import sys
    if "-client" in sys.argv :
        client = RPCClient("127.0.0.1", 22322)
        print "hello() =", client.hello()
        print "add(2, 22) =", client.add(2, 22)
        print "test(2) =", client.test(2)
        print "exception(22)",
        try :
            v = client.exception(22)
            print "=", v, "(should throw exception!)"
        except Exception as x :
            print "throws", x
        print "getargs(1, 2, 3, a=4, b=5) =", client.getargs(1, 2, 3, a=4, b=5)
    else :
        print "Serving at %s:%s" % (HOST, PORT)
        RPCServer((HOST, PORT), Test()).serve_forever()
