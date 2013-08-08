##chat Service
import service
import message
import hash_util
import random
import rsa


from pyDes import *


CHAT_SERVICE = "CHAT"
KEYSIZE = 24

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
        d = triple_des(self.key, padmode=PAD_PKCS5)
        return d.encrypt(hash_to_sign)

    def validate(self, msg, signature):
        return signature == self.sign(msg)

    @classmethod
    def generate_new(cls, handle):
        (pubkey, privkey) = rsa.newkeys(512)
        pubkey_str = hex(pubkey.n)[:-1]+"?"+hex(pubkey.e)[:-1]
        myhash = hash_util.hash_str(pubkey_str)
        return UserInfo(handle,myhash,pubkey,privkey)

    def pub_key_str(self):
        return hex(self.publickey.n).replace("L", "")+"?"+hex(self.publickey.e).replace("L", "")

    def private_key_str(self):
        return '%(n)x?%(e)x?%(d)x?%(p)x?%(q)x' % self.privatekey

    @classmethod
    def from_secret(cls, string):
        parts = string.split(":")
        #print parts
        if len(parts) <= 3:
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
        super(ChatMessage,self).__init__(self, CHAT_SERVICE, "MSG")
        self.origin_node = origin_node  # node that just sent this message
        self.destination_key = destination_key  # the key we're trying to find the node responsible for
        self.reply_to = requester
        self.sender = sender
        self.recipient = recipient
        self.DESKEY = ChatMessage.decode_DES_key(random.randint(0,2**(8*24)))
        self.message = message
        self.signature = signature

    @classmethod
    def decode_DES_key(cls,keyInt):
        results = []
        for i in range(0,KEYSIZE):
            results.append(chr(keyInt%256))
            keyInt/=256
        return results

message.register(ChatMessage)

class ChatService(service.Service):
    def __init__(self):
        super(ChatService, self).__init__()
        self.myinfo = None
        self.friends = []
        self.context = None
        print "Enter contacts file password:"
        mypass = raw_input()
        try:
            print "loading config!"
            file_load = load_preferences("userinfo/data.txt",password=mypass)
            self.myinfo = file_load[0]
            if len(file_load) > 1:
                self.friends = file_load[1:]
        except IOError:
            print "I did not find a config file."
            print "I am generating a new user and config file."
            print "please enter a password:"
            newpass = raw_input()
            print "ok, making a new user:"
            print "enter your desired handle:"
            handle = raw_input()
            self.myinfo = UserInfo.generate_new(handle)
            write_preferences("userinfo/data.txt",[self.myinfo],password=newpass)

    def handle_message(self, msg):
        return True

    def attach_to_console(self):
        ### return a list of command-strings
        return ["send", "add"]

    def handle_command(self, comand_st, arg_str):
        ### one of your commands got typed in
        pass

    def add_friend(self,instr):
        self.friends.append(UserInfo)

def load_preferences(fileloc, password="None"):
    output = []
    with open(fileloc,'rb') as pref_file:
        contents = pref_file.read()
    print "in length", len(contents)

    passkey_int = int(hash_util.hash_str(password).key,16)
    passkey_des = ChatMessage.decode_DES_key(passkey_int)
    d = triple_des(passkey_des, padmode=PAD_PKCS5)
    contents = d.decrypt(contents)
    lines = contents.split("\n")[:-1] 
    for l in lines:
        output.append(UserInfo.from_secret(l))
    return output

def write_preferences(fileloc, userlist, password="None"):
    pref_file = file(fileloc,"wb+")
    outstr = ""
    for u in userlist:
        outstr+=u.gen_secret(True)+"\n"
    passkey_int = int(hash_util.hash_str(password).key,16)
    passkey_des = ChatMessage.decode_DES_key(passkey_int)
    d = triple_des(passkey_des, padmode=PAD_PKCS5)
    contents = d.encrypt(outstr)
    with open(fileloc,'w+') as pref_file:
        pref_file.write(contents)
    print "outlength", len(contents)

#test = UserInfo.generate_new("Test")
#c = ChatMessage(None, None, None, None, None, None, None)
#print test.private_key_str()
#print test.gen_secret(True)
#test2 = UserInfo.from_secret("Test:0x597cc6cf16675785c80061d4a87c2ccd45a9f69d:0xa4ce4c6ee535851a52725cd2b7768517f294038bac0d857e64c8dacc6cd1250d8015a498b7fe24610c0dd566ac705329946b637b185f76fd30eb8254ec3f9da3?0x10001:a4ce4c6ee535851a52725cd2b7768517f294038bac0d857e64c8dacc6cd1250d8015a498b7fe24610c0dd566ac705329946b637b185f76fd30eb8254ec3f9da3?10001?1bfdb9f79fd07e41e13cf14d0cc2018af6b57300b70138ea25be038372fbd9e384e1888918987107a69226a181521272b1c1cba8f63e1da6b6396e60b75f6461?a9cb2188065f5661f3fbe872c00a88e481d6789b5c4ec7d5cc5c6a10e3a70cf35a73?f87ae6e6238f4256386521ec47b47b21aa0e70fcc14f1095bf5b6d5bf411")
#crypto = test.encrypt("hello world")
#print crypto
#print test.decrypt(crypto)
#write_preferences("userinfo/data.txt",[test],password="mypass")

