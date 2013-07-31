#simpler networking solution
from SocketServer import *
import threading
import socket
import node
import message
from Queue import *
import time

CHUNKSIZE = 64

##stolen from http://code.activestate.com/recipes/574454-thread-pool-mixin-class-for-use-with-socketservert/
class ThreadPoolMixIn(ThreadingMixIn):
    '''
    use a thread pool instead of a new thread on every request
    '''
    numThreads = 10
    allow_reuse_address = True  # seems to fix socket.error on server restart

    def serve_forever(self):
        '''
        Handle one request at a time until doomsday.
        '''
        # set up the threadpool
        self.requests = Queue(self.numThreads)

        for x in range(self.numThreads):
            t = threading.Thread(target = self.process_request_thread)
            t.setDaemon(1)
            t.start()

        # server main loop
        while True:
            self.handle_request()
            
        self.server_close()

    
    def process_request_thread(self):
        '''
        obtain request from queue instead of directly from server socket
        '''
        while True:
            ThreadingMixIn.process_request_thread(self, *self.requests.get())

    
    def handle_request(self):
        '''
        simply collect requests and put them on the queue for the workers.
        '''
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))

class ThreadedServer(ThreadPoolMixIn, TCPServer):
    pass


class NETWORK_SERVICE(object):
    def sender_loop(self):
            while True:
                priority, dest, msg = self.tosend.get(True)
                try:
                    self.client_send(dest,msg)
                except:
                    print "!!there was a networking issue!!"
                self.tosend.task_done()

    def send_message(self,msg,dest):
        msg_pack = (msg.priority,dest,msg)
        self.tosend.put(msg_pack,True)
        

    def __init__(self,HOST="localhost",PORT=9000):
        # Create the server, binding to localhost on port 9999
        self.server = ThreadedServer((HOST, PORT), MyTCPHandler)
        self.tosend = PriorityQueue()
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        t = threading.Thread(target=self.server.serve_forever)
        t.daemon = True
        t.start()
        for i in range(0,4):
            t2 = t = threading.Thread(target=self.sender_loop)
            t2.daemon = True
            t2.start()

    def stop(self):
        self.server.shutdown()

    def update_messages_in_queue(self, failed_node):
        hold = []
        while not self.tosend.empty():
            temp = self.tosend.get()
            self.tosend.task_done()
            if temp[1] == failed_node:
                node.message_failed(temp[2],temp[1])
            else:
                hold.append(temp)
        for h in hold:
            self.tosend.put()

    def client_send(self, dest, msg):
        #pass#print msg.service, msg.type, str(dest)
        HOST = dest.IPAddr
        PORT = dest.ctrlPort
        DATA = msg.serialize()
        ##pass#print len(DATA)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        length = len(DATA)
        padding = CHUNKSIZE-length%CHUNKSIZE
        DATA+=" "*padding
        length = len(DATA)/CHUNKSIZE
        byte1 = length >> 8
        byte2 = length % (2**8)
        ###pass#print byte1, byte2
        b1 = chr(byte1)
        b2 = chr(byte2)
        ###pass#print b1, b2, ord(b1), ord(b2)
        #pass#print "<",
        try:
            # Connect to server and send data
            sock.connect((HOST, PORT))
            sock.send(b1)
            sock.send(b2)
            ack = ""
            while len(ack) < 1:
                ack = sock.recv(1)
            sock.send(DATA)
                
            
            # Receive data from the server and shut down
            ack=""
            while len(ack) < 1:
                ack = sock.recv(1)
        except socket.error:
            ##pass#print e
            #sock.close()
            pass#print "SOCKET ERROR"
            node.message_failed(msg,dest)
            #self.update_messages_in_queue(dest)
        finally:
            #pass#print ">",
            sock.close()
            ##pass#print DATA[-20:],len(DATA)%8
            return True


class MyTCPHandler(BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def __init__(self, request, client_address, server):
        self.data = ""
        BaseRequestHandler.__init__(self, request, client_address, server)



    def handle(self):
        # self.request is the TCP socket connected to the client
        b1 = ""
        b2 = ""
        #pass#print "[",
        while len(b1) == 0:
            b1 = self.request.recv(1)
        while len(b2) == 0:
            b2 = self.request.recv(1)
        #pass#print b1, b2
        b1 = ord(b1)
        b2 = ord(b2)
        length = ((b1 << 8) + b2)*CHUNKSIZE
        maxlength = length/CHUNKSIZE
        self.request.send("0")
        data = ""
        data0=""
        while length > 0:
            ###pass#print length
            buff = CHUNKSIZE
            if length < CHUNKSIZE:
                buff =length
            data0 = self.request.recv(buff)
            length-=len(data0)
            data+=data0
        self.request.send("0")
        old_length = len(data)
        data = data.rstrip(" ")
        ##pass#print "incoming length: " +str(len(data))
        msg = message.Message.deserialize(data)
        #pass#print "]",
        node.handle_message(msg)


    def handle_error(self, request, client_address):
        pass#print client_address,"tried to talk to me and failed"
