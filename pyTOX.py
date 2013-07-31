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

from Crypto.PublicKey import RSA

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
    database_name = str(node.thisNode.key)+".db"
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
    state = "console" #state can also be chat
    command_dict = {}


def main():
    myip = myIP()
    node.IPAddr = myip
    args = sys.argv
    local_port = 10000
    done = False
    while not done:
        try:
            setup_Node(addr=myip,port=local_port)
            done = True
        except:
            local_port+=1
    servers = file("userinfo/entryPoints.txt")
    server_data = servers.read().split("/n")
    for l in server_data:
        server, port = l.split(":",1)
        join_ring(server, int(port))
    node.startup()
    console()

if __name__ == "__main__":
    main()

