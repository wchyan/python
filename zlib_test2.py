#!/usr/bin/python
# -*- coding: utf-8 -*-

import zlib, urllib
 
fp = urllib.urlopen('http://www.baidu.com')    # 访问的到的网址。
data = fp.read()
fp.close()
 
#---- 压缩数据流
str1 = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
str2 = zlib.decompress(str1)
print '原始数据长度：', len(data)
print '-' * 30
print 'zlib.compress压缩后：', len(str1)
print 'zlib.decompress解压后：', len(str2)
print '-' * 30
 
#---- 使用Compress, Decompress对象对数据流进行压缩/解压缩
com_obj = zlib.compressobj(zlib.Z_BEST_COMPRESSION)
decom_obj = zlib.decompressobj()
 
str_obj = com_obj.compress(data)
str_obj += com_obj.flush()
print 'Compress.compress压缩后：', len(str_obj)
 
str_obj1 = decom_obj.decompress(str_obj)
str_obj1 += decom_obj.flush()
print 'Decompress.decompress解压后：', len(str_obj1)
print '-' * 30
 
#---- 使用Compress, Decompress对象，对数据进行分块压缩/解压缩。
com_obj1 = zlib.compressobj(zlib.Z_BEST_COMPRESSION)
decom_obj1 = zlib.decompressobj()
chunk_size = 30;
 
#原始数据分块
str_chunks = [data[i * chunk_size:(i + 1) * chunk_size] \
    for i in range((len(data) + chunk_size) / chunk_size)]
 
str_obj2 = ''
for chunk in str_chunks:
    str_obj2 += com_obj1.compress(chunk)
str_obj2 += com_obj1.flush()
print '分块压缩后：', len(str_obj2)
 
#压缩数据分块解压
str_chunks = [str_obj2[i * chunk_size:(i + 1) * chunk_size] \
    for i in range((len(str_obj2) + chunk_size) / chunk_size)]
str_obj2 = ''
for chunk in str_chunks:
    str_obj2 += decom_obj1.decompress(chunk)
str_obj2 += decom_obj1.flush()
print '分块解压后：', len(str_obj2)
  
'''
# ---- 结果 ------------------------
原始数据长度： 5783
------------------------------
zlib.compress压缩后： 1531
zlib.decompress解压后： 5783
------------------------------
Compress.compress压缩后： 1531
Decompress.decompress解压后： 5783
------------------------------
分块压缩后： 1531
分块解压后： 5783
'''
