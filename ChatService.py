##chat Service
import service
import message
import hash_util
import random
import rsa
import time
import hashlib
from worker_handler import WorkerManager
from pyDes import *


CHAT_SERVICE = "CHAT"
KEYSIZE = 24

subscribed_channels = {"dev": 0.0}




class UserInfo(object):
    def __init__(self, handle, hashid, publickey, privatekey = None):
        self.handle = handle
        self.hashid = hashid
        self.publickey = publickey
        self.privatekey = privatekey

    def encrypt(self,msg):
        return rsa.encrypt(msg, self.publickey)
        #d = triple_des(self.key)
        #return d.encrypt(msg, padmode=PAD_PKCS5)

    def decrypt(self,msg):
        return rsa.decrypt(msg, self.privatekey)
        #d = triple_des(self.key, padmode=PAD_PKCS5)
        #return d.decrypt(msg)

    def sign(self, msg):
        hash_to_sign = hash_util.hash_str(msg).key
        return rsa.encrypt(hash_to_sign, self.publickey)

    def validate(self, msg, signature):
        return signature == self.sign(msg)

    @classmethod
    def generate_new(cls, handle):
        (pubkey, privkey) = rsa.newkeys(1024)
        pubkey_str = hex(pubkey.n)[:-1]+"?"+hex(pubkey.e)[:-1]
        myhash = hash_util.hash_str(pubkey_str)
        return UserInfo(handle,myhash,pubkey,privkey)

    def pub_key_str(self):
        return hex(self.publickey.n).replace("L", "")+"?"+hex(self.publickey.e).replace("L", "")

    def private_key_str(self):
        return '%(n)x?%(e)x?%(d)x?%(p)x?%(q)x' % self.privatekey

    @classmethod
    def from_secret(cls, string):
        if string == "NONE":
            return None
        parts = string.split(":")
        #print parts
        if len(parts) < 3:
            return None
        handle = parts[0]
        hashid = hash_util.Key(parts[1])
        keyparts = parts[2].split("?")
        pubkey = rsa.PublicKey(int(keyparts[0],16),int(keyparts[1],16))
        prikey = None
        if len(parts) == 4:
            keyparts = parts[3].split("?")
            keyints = map( lambda x: int(x,16), keyparts)
            prikey = rsa.PrivateKey(keyints[0],keyints[1],keyints[2],keyints[3],keyints[4])
        return UserInfo(handle, hashid, pubkey, prikey)

    def gen_secret(self,prikey=False):
        if prikey and self.privatekey:
            return self.handle+":"+str(self.hashid.key)+":"+self.pub_key_str()+":"+self.private_key_str()
        else:
            return self.handle+":"+str(self.hashid.key)+":"+self.pub_key_str()

class ChatMessage(message.Message):
    def __init__(self, origin_node, destination_key, requester, sender, recipient, message, signature):
        super(ChatMessage,self).__init__(CHAT_SERVICE, CHAT_SERVICE)
        self.origin_node = origin_node  # node that just sent this message
        self.destination_key = destination_key  # the key we're trying to find the node responsible for
        self.reply_to = requester
        self.sender = sender
        self.recipient = recipient
        self.DESKEY = ChatMessage.decode_DES_key(random.randint(0,2**(8*24)))
        self.message = message
        self.signature = signature
        self.encrypted = False
        self.secured = False
    @classmethod
    def decode_DES_key(cls,keyInt):
        results = []
        for i in range(0,KEYSIZE):
            results.append(chr(keyInt%256))
            keyInt/=256
        return results
    @classmethod
    def encode_DES_key(cls,keylist):
        results = 0L
        c = 0
        for i in keylist:
            results+=ord(i)<<(8*c)
            c+=1
        return results
    @classmethod
    def passwrd_to_3DES(cls, passwrd):
        m = hashlib.md5()
        m.update(passwrd)
        result = m.digest()
        keyint = cls.encode_DES_key(result)
        return cls.decode_DES_key(keyint)

    def encrypt(self):
        if not self.encrypted:
            d = triple_des(self.DESKEY)
            self.message = d.encrypt(self.message, padmode=PAD_PKCS5)
            self.encrypted = True
            print "encrypting"
        else:
            raise Exception("Encrypting an already encrypted message")

    def decrypt(self):
        #return rsa.decrypt(msg, self.privatekey)
        if self.encrypted:
            d = triple_des(self.DESKEY)
            self.message = d.decrypt(self.message, padmode=PAD_PKCS5)
            self.encrypted = False
            print "decrypting"
        else:
            raise Exception("Decrypting an already decrypted message")

    def secure(self, dest):
        if not self.secured and self.encrypted == True:
            self.DESKEY = dest.encrypt(str(ChatMessage.encode_DES_key(self.DESKEY)))
            self.secured = True
        elif self.encrypted == False:
            raise Exception("securing an unencrypted message")
        else:
            raise Exception("Re-securing a secure message message")
    def desecure(self, dest):
        if self.secured and self.encrypted == True:
            self.DESKEY = ChatMessage.decode_DES_key(int(dest.decrypt(self.DESKEY)))
            self.secured = False
        elif self.encrypted == False:
            raise Exception("descuring an unencrypted message")
        else:
            raise Exception("de-securing an unsecure message message")

message.register(ChatMessage)

class Channel(object):
    def __init__(self, hashid):
        self.hashid = hashid
        self.record = []
        self.killtime = 60*5 #messages older then 5 minutes get dropped

    def get_messages(self, lastime):
        #now =  time.time()
        output = []
        for r in self.record:
            ptime, msg = r
            #print ptime, lastime, now, ptime >=lastime
            if ptime >= lastime:
                output.append(msg)
            #print output
        return output

    def put_message(self, msg):
        now = time.time()
        #print "putmsg", now, msg
        self.record.append([now, msg])
        for r in self.record:
            ptime, msg = r
            if ptime < now - self.killtime:
                self.record.remove(r)
                #print "killedmsg"



class ChatService(service.Service):
    def __init__(self):
        super(ChatService, self).__init__()
        self.myinfo = None
        self.friends = []
        self.context = None
        self.service_id = CHAT_SERVICE
        self.open_pings = {}
        self.channels = {}
        self.channelsurfer = WorkerManager()
        self.channelsurfer.ideal_threads = 1
        self.channelsurfer.target = self.poll_channels
        self.channelsurfer.ishandler = False
        

        try:
            print( "loading config!")
            file_load = load_preferences("userinfo/data.txt")
            self.myinfo = file_load[0]
            if len(file_load) > 1:
                self.friends = file_load[1:]
        except IOError:
            print( "I did not find a config file.")
            print( "I am generating a new user and config file.")
            print( "enter your desired handle:")
            handle = raw_input()
            self.myinfo = UserInfo.generate_new(handle)
            write_preferences("userinfo/data.txt",[self.myinfo])
        print( "you are logged in as:", self.myinfo.handle)

    def get_channel_from_hashid(self, hid):
        for c in subscribed_channels.keys():
            if hash_util.hash_str(c) == hid:
                return c
        return None

    def handle_message(self, msg):
        #print "got", msg, msg.recipient

        #print to, to.hashid, self.myinfo.hashid
        if msg.type == "CPOLL":
            self.handle_CPOLL(msg)
            return True
        if msg.type == "CRESP":
            cname = self.get_channel_from_hashid(msg.get_content("CHANNEL"))
            if len(msg.message) > 0:
                print msg.message
                for m in msg.message:
                    #print m
                    ckey = ChatMessage.passwrd_to_3DES(cname)
                    chash = hash_util.hash_str(cname)
                    m.DESKEY = ChatMessage.passwrd_to_3DES(cname)
                    print len(m.message)
                    m.decrypt()
                    #cname = self.get_channel_from_hashid(chash)
                    print "["+cname+"]", m.message
                subscribed_channels[cname] = msg.get_content("pollTime")
            return True
        if msg.type == "CPOST":
            self.handle_CPOST(msg)
            return True
        to = UserInfo.from_secret(msg.recipient)
        if not hash_util.hash_equal(to.hashid,self.myinfo.hashid):
            print("got somebody else's message")
            return True
        if msg.type == "CHAT":
            origin = UserInfo.from_secret(msg.sender)
            local_origin = self.get_friend_from_hash(origin.hashid)
            if local_origin is None:
                print("You got a message from a user outside your friend list")
                return
            msg.desecure(self.myinfo)
            msg.decrypt()
            print( "{"+local_origin.handle+"} "+msg.message)
            return True
        if msg.type == "PING":
            msg.desecure(self.myinfo)
            msg.decrypt()
            to = UserInfo.from_secret(msg.sender)
            pid = msg.message
            if pid in self.open_pings.keys():
                now = time.time()
                delta = now - self.open_pings[pid]
                print self.get_friend_from_hash(to.hashid).handle, "is online", delta
            else:
                print to.handle, "is online and has pinged you"
                newmsg = ChatMessage(self.owner, to.hashid, self.owner, self.myinfo.gen_secret(False), to.gen_secret(False), pid, to.sign(pid) )
                newmsg.type = "PING"
                newmsg.encrypt()
                newmsg.secure(to)
                self.send_message(newmsg,None)
            return True

        return True

    def get_friend(self,handle):
        for f in self.friends:
            if f.handle == handle:
                return f
        print "Friend Not Found:", handle
        return None

    def get_friend_from_hash(self,hashid):
        for f in self.friends:
            if hash_util.hash_equal(f.hashid, hashid):
                return f
        return None

    def attach_to_console(self):
        ### return a list of command-strings
        return ["send", "add", "who","whoami", "save", "rename", "ping", "listen","post"]

    def handle_command(self, comand_st, arg_str):
        global subscribed_channels
        if not self.channelsurfer.running:
            self.channelsurfer.start()
        ### one of your commands got typed in
        if comand_st == "listen":
            chan = arg_str
            subscribed_channels[chan] = 0.0
        if comand_st == "post":
            chan, msg = arg_str.split(" ",1)
            ckey = ChatMessage.passwrd_to_3DES(chan)
            chash = hash_util.hash_str(chan)
            newmsg = ChatMessage(self.owner, chash, self.owner, self.myinfo.gen_secret(False), "NONE", msg, "NONE" )
            newmsg.DESKEY = ChatMessage.passwrd_to_3DES(chan)
            newmsg.type = "CPOST"         
            newmsg.encrypt()
            self.send_message(newmsg, None)

        if comand_st == "add": 
            self.add_friend(arg_str)
        if comand_st == "send":
            args = arg_str.split(" ",1)
            to_str = args[0]
            to = self.get_friend(to_str)
            if to is None:
                return
            try:
                msg = args[1]
            except:
                print("you need a message")
                return
            newmsg = ChatMessage(self.owner, to.hashid, self.owner, self.myinfo.gen_secret(False), to.gen_secret(False), msg, to.sign(msg) )
            newmsg.encrypt()
            newmsg.secure(to)
            self.send_message(newmsg, None)
        if comand_st == "whoami":
            print( self.myinfo.gen_secret(False))
        if comand_st == "who":
            print("Your friends are:")
            for f in self.friends:
                print(f.handle)
            for f in self.friends:
                self.ping(f.handle)
        if comand_st == "save":
            mylist = [self.myinfo]+self.friends
            write_preferences("userinfo/data.txt",mylist)
        if comand_st == "rename":
            args = arg_str.split(" ")
            old = args[0]
            new = args[1]
            f = self.get_friend(old)
            if not f is None:
                f.handle = new
                print(old+" has been renamed "+new)
        if comand_st == "ping":
            user = arg_str
            self.ping(user)


    def ping(self, user):
        to = self.get_friend(user)
        msg = str(random.randint(0,2**20))
        if not to is None:
            newmsg = ChatMessage(self.owner, to.hashid, self.owner, self.myinfo.gen_secret(False), to.gen_secret(False), msg, to.sign(msg) )
            newmsg.type = "PING"
            newmsg.encrypt()
            newmsg.secure(to)
            self.open_pings[msg] = time.time()
            self.send_message(newmsg, None)

    def add_friend(self,instr):
        self.friends.append(UserInfo.from_secret(instr))


    def handle_CPOST(self, msg):
        print "got a post", msg.message
        cid = msg.destination_key
        if cid in self.channels.keys():
            self.channels[cid].put_message(msg)
        else:
            print "new channel made"
            self.channels[cid] = Channel(cid)
            self.channels[cid].put_message(msg)

    def handle_CPOLL(self, msg):
        cid = msg.destination_key
        if cid in self.channels.keys():
            output = self.channels[cid].get_messages(float(msg.message))
            newmsg = ChatMessage(self.owner, msg.reply_to.key, self.owner, "NONE", msg.reply_to, output, "NONE" )
                                #origin_node, destination_key, requester, sender, recipient, message, signature):
            #newmsg.DESKEY = ChatMessage.passwrd_to_3DES(c)
            newmsg.type = "CRESP"
            newmsg.add_content("CHANNEL",cid)
            newmsg.add_content("pollTime",time.time())
            self.send_message(newmsg, msg.reply_to)
        else:
            pass #do nothing, there is no such channel yet

    def poll_channels(self):
        global subscribed_channels
        for c in subscribed_channels.keys():
           # print "pollin", c
            lasttime = subscribed_channels[c]
            chash = hash_util.hash_str(c)
            newmsg = ChatMessage(self.owner, chash, self.owner, self.myinfo.gen_secret(False), "NONE", str(lasttime), "NONE" )
            newmsg.type = "CPOLL"         
            self.send_message(newmsg, None)
            
        time.sleep(1)
        #print "polled", subscribed_channels

def load_preferences(fileloc):
    output = []
    with open(fileloc,'rb') as pref_file:
        for l in pref_file:
            output.append(UserInfo.from_secret(l))
        print output
    return output

def write_preferences(fileloc, userlist, password=None):
    pref_file = file(fileloc,"w+")
    outstr = ""
    for u in userlist:
        outstr+=u.gen_secret(True)+"\n"
    with open(fileloc,'w+') as pref_file:
        pref_file.write(outstr)
    #print "outlength", len(contents)

#test = UserInfo.generate_new("Test")
#c = ChatMessage(None, None, None, None, None, None, None)
#print test.private_key_str()
#print test.gen_secret(True)
#test2 = UserInfo.from_secret("Test:0x597cc6cf16675785c80061d4a87c2ccd45a9f69d:0xa4ce4c6ee535851a52725cd2b7768517f294038bac0d857e64c8dacc6cd1250d8015a498b7fe24610c0dd566ac705329946b637b185f76fd30eb8254ec3f9da3?0x10001:a4ce4c6ee535851a52725cd2b7768517f294038bac0d857e64c8dacc6cd1250d8015a498b7fe24610c0dd566ac705329946b637b185f76fd30eb8254ec3f9da3?10001?1bfdb9f79fd07e41e13cf14d0cc2018af6b57300b70138ea25be038372fbd9e384e1888918987107a69226a181521272b1c1cba8f63e1da6b6396e60b75f6461?a9cb2188065f5661f3fbe872c00a88e481d6789b5c4ec7d5cc5c6a10e3a70cf35a73?f87ae6e6238f4256386521ec47b47b21aa0e70fcc14f1095bf5b6d5bf411")
#crypto = test.encrypt("hello world")
#print crypto
#print test.decrypt(crypto)
#write_preferences("userinfo/data.txt",[test],password="mypass")

