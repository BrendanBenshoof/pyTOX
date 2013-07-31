#python class to hold user info
import base64
import cPickle as Pickle
import hash_util
#import M2Crypto

class UserInfo(object): #this class is just a struct you can use transmit user info with
	def __init__(self):
		self.handle = None
		self.hashloc = None
		self.netLoc = None
	@classmethod
	def parse(cls,userkey):
		self = cls()
		parts = userkey.split(":")
		self.handle = parts[0]
		keystr = base64.b64decode(parts[1])
		self.hashloc = hash_util.Key(keystr)
		self.netLoc = None
		return self
	@classmethod
	def generate(cls,handle):
		newuser = cls()
		newuser.handle = handle
		newuser.hashloc = hash_util.hash_str(handle)
		newuser.netloc = None
		return newuser
	
	def __str__(self):
		keystr = base64.b64encode(self.hashloc.key)
		return self.handle+":"+keystr
