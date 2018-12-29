#!/usr/bin/python

from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import urllib2
import time

### map
def PoolFun(url):
    print url
    urllib2.urlopen(url)

urls = [ 'http://www.baidu.com',
        'http://www.sina.com',
        'http://www.163.com',
        'http://news.163.com',
        'http://map.baidu.com',
        'http://python.jobbole.com',
        'http://www.zhihu.com']


pool = ThreadPool(4) # Sets the pool size to 4
result = pool.map(PoolFun, urls)
pool.close()
pool.join()

print 'Pool  :', result

### map
def CalData(data):
    return data * 2

pool = ThreadPool(4) # Sets the pool size to 4
result = pool.map(CalData, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
pool.close()
pool.join()

print 'Pool  :', result

### apply_async
def func(msg):
    for i in xrange(3):
        print "func ", i, msg
        time.sleep(1)
    return "done " + msg

pool = ThreadPool(processes=4)
result = []
for i in xrange(20):
    msg = "hello %d" %(i)
    result.append(pool.apply_async(func, (msg, )))
pool.close()
pool.join()

for res in result:
    print res.get()
    print "Sub-process(es) done."
