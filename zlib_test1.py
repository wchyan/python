#!/usr/bin/python

import zlib, urllib

fp = urllib.urlopen('http://www.baidu.com')
str = fp.read()
fp.close()
   
str1 = zlib.compress(str, zlib.Z_BEST_COMPRESSION)
str2 = zlib.decompress(str1)

print len(str)
print len(str1)
print len(str2)

print str2
