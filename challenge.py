from Crypto.PublicKey import RSA
import os
import random
import pickle
import urllib2

# sorry, ignore this bit, it's just a hack to get past SSL/CERT issues with
# my install of Python :(
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# mini random.org library, fetches a random set of strings, each 20 characters
# wide. defaults to pretty close to 2048 bytes of data, but you can change that
# when calling getrand().

class random_org(object):
    def __init__(self):
        #self.url = 'http://localhost:3000/strings.txt' # for when you are quota'd by random.org
        self.url = 'https://www.random.org/strings/?num=__NUM__&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new'

    def getrand(self, num=int(2048/20)):
        u = self.url.replace('__NUM__', str(num))
        return urllib2.urlopen(u, context=ctx).read().splitlines()



# once we get data from random.org, let's pickle it locally and use it again
# (just so we don't hit our quota... in real life you wouldn't want to do
# this for generating key material, heh).
class PersistedRandData(object):
    def __init__(self, filename):
        self.filename = filename + '.prd'
        self.data = {}

    def set_data(self, data):
        self.data['data'] = data
        self.data['pos'] = 0

    def read_data(self, size):
        pos = self.data['pos']
        # there's a limit to the data, have to wrap around
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


#### challenge 2(a) # generate a key pair from the random data.

# requires this callback to get at random.org bits we've saved.
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



#### challenge 2(b), create BMP

rdata.read_data(256)
from PIL import Image

img = Image.new( 'RGB', (128,128), "black") # create a new black image
pixels = img.load() # create the pixel map

for i in range(img.size[0]):    # for every pixel:
    for j in range(img.size[1]):
        # read from our random data three characters at a time, and determine
        # the ascii index for each.
        g = (ord(a) for a in tuple(rdata.read_data(3)))
        pixels[i,j] = (g.next(), g.next(), g.next()) # set the random color

#img.show()
img.save('rand.bmp')
