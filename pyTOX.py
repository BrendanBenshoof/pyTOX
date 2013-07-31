#!/usr/bin/env python
###Startup and commandline file
import service
import hash_util
import random
import simple_network
import node
import time
import Queue
from threading import *
import sys
import chat_service
import user

from termcolor import colored

from globals import *

import json
from urllib2 import urlopen

local_mode=False
userinfo=None

def myIP():
    if not local_mode:
        myip = json.load(urlopen('http://httpbin.org/ip'))['origin']
        pass#print "just got my ip:", myip
        return myip
    else:
        return "127.0.0.1"
    

# backwards-compatibility use of global vars...encapsulation is easily
# possible by ensuring all functionality lives in a service with a reference
# to router which would then be instantiated in main()
services = {}
commands = {}

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

def setup_Node(addr="localhost", port=None):
    node.IPAddr = addr
    node.ctrlPort = port
    node.thisNode = node.Node_Info(node.IPAddr, node.ctrlPort)
    #node.net_server = dummy_network.start(node.thisNode, node.handle_message)
    node.net_server = simple_network.NETWORK_SERVICE("", node.ctrlPort)
    #### setup services here
    #database_name = str(node.thisNode.key)+".db"
    add_service(service.Internal_Service())
    add_service(service.ECHO_service())
    add_service(chat_service.ChatService())
    ####
    attach_services()


def join_ring(node_name, node_port):
    othernode = node.Node_Info(node_name, node_port)
    node.join(othernode)

def no_join():
    node.create()

def console():##need to re-write into something CURSE-y
    cmd = "-"
    state = "command" #state can also be chat
    command_dict = {}
    running = True
    while(running):
        print "["+colored("COMMAND:","blue")+"]:",
        user_input = raw_input()
        if user_input == "exit" or user_input == "quit":
            break
        try:
            mycommand, args = user_input.split(" ",1)
            service_to_handle = commands[mycommand]
            service_to_handle.handle_command(mycommand, args)
        except ValueError:
            pass


def main():
    myip = myIP()
    node.IPAddr = myip
    args = sys.argv
    local_port = 10000
    done = False
    try:
        setup_Node(addr=myip,port=local_port)
        done = True
    except:
        polite_print("!!There was a fatal networking error!!")
        return
    polite_print("I settled on using port:"+str(local_port))
    node.create()
    node.startup()
    servers = file("userinfo/entryPoints.txt")
    server_data = servers.read().split("\n")
    for l in server_data:
        if( len(l) > 0):
            polite_print("trying: "+l)
            addr, port, hash_str= l.split(":")
            port = int(port)
            n = node.Node_Info(addr,port)
            n.key.key = hash_str
            
            #services[SERVICE_INTERNAL].handle_command("connect",l)

    
    console()

if __name__ == "__main__":
    main()

