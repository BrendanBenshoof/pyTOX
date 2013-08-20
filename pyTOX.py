#!/usr/bin/env python
###Startup and commandline file
import service
import hash_util
import random
import simple_network
import node
import time
import Queue
import ChatService
from threading import *
import sys



import json
from urllib2 import urlopen

local_mode=False

def myIP():
    if not local_mode:
        myip = json.load(urlopen('http://httpbin.org/ip'))['origin']
        print "just got my ip:", myip
        return myip
    else:
        return "127.0.0.1"
    

# backwards-compatibility use of global vars...encapsulation is easily
# possible by ensuring all functionality lives in a service with a reference
# to router which would then be instantiated in main()
services = {}
commands = {}
myhashkey = None

def add_service(service_object):
    s_name = service_object.service_id
    services[s_name] = service_object

def attach_services():
    for s_name in services.keys():
        node.add_service(services[s_name])
        commands_list = services[s_name].attach_to_console()
        if not commands_list is None:
            for c in commands_list:
                commands[c] = services[s_name]
chat = None

def setup_Node(addr="localhost", port=None):
    global myhashkey, chat
    node.IPAddr = addr
    node.ctrlPort = port
    chat = ChatService.ChatService()
    myhashkey = chat.myinfo.hashid
    node.thisNode = node.Node_Info(node.IPAddr, node.ctrlPort, myhashkey)
    #node.net_server = dummy_network.start(node.thisNode, node.handle_message)
    node.net_server = simple_network.NETWORK_SERVICE("", node.ctrlPort)
    #### setup services here
    #database_name = str(node.thisNode.key)+".db"
    #add_service(db.Shelver(database_name))
    add_service(service.Internal_Service())
    
    add_service(chat)

    #add_service(service.ECHO_service())
    #add_service(Topology_Service.Topology())
    #add_service(filesystem_service.FileSystem())
    #add_service(map_reduce.Map_Reduce_Service())
    ####
    attach_services()


def join_ring(node_name, node_port):
    othernode = node.Node_Info(node_name, node_port)
    node.join(othernode)

def no_join():
    node.create()

class Context(object): #a context describes a place a user can type, and the message has to go somewhere
    def __init__(self, name, type, dest):
        self.name = name
        self.type = type
        self.dest = dest
        self.chatserv = chat

    def focus(self):
        if self.type == "channel":
            print "chatting on channel",self.dest
        else:
            print "chatting with", self.dest

    def say(self, mstr):
        command = ""
        args = ""
        if self.type == "chat":
            command = "/send"
            args = self.dest+" "+mstr
        elif self.type == "channel":
            command = "/post"
            args = args = self.dest+" "+mstr
        #print "say", command, args
        mytarget = chat.handle_command(command, args)
        t = Thread(target=mytarget)
        t.daemon = True
        t.start()       


def console():
    if not chat.channelsurfer.running:
        chat.channelsurfer.start()
    curr_context = Context("dev","channel","dev")
    curr_context.focus()
    userinput = raw_input()
    while not ( userinput == "/q" or userinput == "/Q"):
        
        if len(userinput) >0 and userinput[0]!= "/":#handle raw_input
            curr_context.say(userinput)
        elif len(userinput) >0  and userinput[0]== "/": #this is a command
            precommand = userinput.split(" ",1)
            command = precommand[0]
            if command == "/chan":
                args = precommand[1]
                curr_context = Context(args, "channel", args)
                curr_context.focus()
                chat.handle_command("/listen",args)
            elif command == "/chat":
                args = precommand[1]
                if not chat.get_friend(args) is None:
                    curr_context.focus()
                    curr_context = Context(args,"chat",args)
            elif command == "/help" or command == "/h" or command == "/?":
                print """
This is the Help Document:
It is mostly a placeholder
commands:
/chat $friendname       --- Directs all input as chat to given friend

/chan $channame         --- Directs all input to the given channel
                            listens to the channel if you are not already

/add $userinfopack      --- given the massive pile of encoded RSA key info 
                            for a user, it adds them as a friend

/listen $channame       --- adds the channel to the list you listen to

/rename $oldnic $newnic --- renames a friend (only shows change in chats
                            not channels)

/ping $friend           --- sends a ping to check if a friend is online

/who                    --- pings all your friends

/whoami                 --- prints the string you need to give other 
                        users in order to add you as a friend
"""
            else:
                args = ""
                if len(precommand) > 1:
                    args = precommand[1]
                mytarget = chat.handle_command(command, args)
                t = Thread(target=mytarget)
                t.daemon = True
                t.start()
        userinput = raw_input("")
    node.net_server.stop()

def main():
    myip = myIP()
    node.IPAddr = myip
    args = sys.argv
    if len(args) > 1 and args[1] != "?":
        local_port = int(args[1]) 
    else: 
        local_port = random.randint(9000, 9999)
        
    other_IP = args[2] if len(args) > 2 else "131.96.49.89"
    other_port = int(args[3]) if len(args) > 3 else 9000

    setup_Node(addr=myip,port=local_port)
    if not other_IP is None and not other_port is None:
        join_ring(other_IP, other_port)
    else:
        no_join()
    node.startup()
    console()

if __name__ == "__main__":
    main()

