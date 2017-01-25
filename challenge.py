from Crypto.PublicKey import RSA
from Crypto.Util import randpool
from Crypto import Random
import os 
import random
import pickle
import urllib2

# NOTE(james) sorry, ignore this bit, it's a hack to get past SSL/CERT issues
# with my install of Python :(
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# mini random.org library
class random_org(object):
    def __init__(self):
        #self.url = 'http://localhost:3000/strings.txt' # for when you are quota'd by random.org
        self.url = 'https://www.random.org/strings/?num=__NUM__&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new'
    
    def getrand(self, num=int(2048/20)):
        u = self.url.replace('__NUM__', str(num))
        return urllib2.urlopen(u, context=ctx).read().splitlines()

# once we get data from random.org, let's pickle it locally and use it again
class PersistedRandData(object):
    def __init__(self, filename):
        self.filename = filename + '.prd'
        self.data = {}

    def set_data(self, data):
        self.data['data'] = data
        self.data['pos'] = 0

    def read_data(self, size):
        pos = self.data['pos']
        if pos + size > len(self.data['data']):
            pos = self.data['pos'] = 0
        self.data['pos'] = pos + size
        return self.data['data'][pos:pos+size]

    def load(self):
        self.data = pickle.load(open(self.filename, 'rb'))
    
    def save(self):
        pickle.dump(self.data, open(self.filename, 'wb'))

    def exists(self):
        return os.path.exists(self.filename)


# check, fetch, cache random data 
rdata = PersistedRandData('rdata')
if not rdata.exists():
    ro = random_org()
    rdata.set_data(''.join(ro.getrand()))
    rdata.save()
else:
    rdata.load()

# generate a key pair from the random data. requires this callback to get at
# random.org bits we've saved.
def rand_gen_callback(n):
    return rdata.read_data(n)

key = RSA.generate(1024, rand_gen_callback)

# make sure things are working like they should
assert key.can_encrypt() is True
pubkey = key.publickey()
assert key.decrypt(pubkey.encrypt('helowrld', 1)) == 'helowrld'

# let's see the keys
print key.exportKey('PEM')
print key.publickey().exportKey()


