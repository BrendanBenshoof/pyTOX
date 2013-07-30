from message import *
from hash_util import *
from Queue import Queue
import node
import os
import time
import service
from user import *
from globals import *
import random

class Chat_Message(Message):
    def __init__(self, origin_node, destination_key, to, fromguy, chat):
        Message.__init__(self, "CHAT", "CHAT")
        self.origin_node = origin_node
        self.destination_key = destination_key
        self.add_content("to",to)
        self.add_content("chat",chat)
        self.add_content("from",fromguy)
        self.reply_to = origin_node

class ChatService(service.Service):
    """docstring for Database"""
    def __init__(self):
        super(ChatService, self).__init__()
        self.service_id = "CHAT"
        self.user = None

    def attach_to_console(self):
        ### return a dict of command-strings
        try:
            myhandle = raw_input("what is your name?")
        except:
            myhandle = "SERVER"+str(random.random() )
        self.user = UserInfo.generate(myhandle)
        self.owner.key = self.user.hashloc
        return ["send"]

    def handle_command(self, command_st, arg_str):
        arglist = arg_str.split(" ",1)
        dest = arglist[0]
        destuser = UserInfo.generate(dest)
        chat = arglist[1]
        msg = Chat_Message(self.owner, destuser.hashloc, destuser.handle,self.user, chat)
        self.send_message(msg, None)

            
    def handle_message(self, msg):
        if not msg.service == self.service_id:
            return False
        if msg.get_content("to") != self.user.handle:
            print "Got somebody else's message"
            return True
        else:
            otherguy = msg.get_content("from").handle
            print otherguy+": " + msg.get_content("chat")
 
