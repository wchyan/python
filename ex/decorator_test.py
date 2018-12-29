#!/usr/bin/python

#http://python.jobbole.com/81683/

#inner func
def outer(some_func):
    def inner():
        print "before some_func"
        ret = some_func() # 1
        return ret + 1
    return inner

def foo():
    return 1


decorated = outer(foo) # 2
print decorated()

class Coordinate(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return "Coord: " + str(self.__dict__)

def add(a, b):
        return Coordinate(a.x + b.x, a.y + b.y)
def sub(a, b):
        return Coordinate(a.x - b.x, a.y - b.y)

one = Coordinate(100, 200)
two = Coordinate(300, 200)
three = Coordinate(-100, -100)
print sub(one, two)
print add(one, three)

def wrapper(func):
    def checker(a, b): # 1
        if a.x < 0 or a.y < 0:
            a = Coordinate(a.x if a.x > 0 else 0, a.y if a.y > 0 else 0)
        if b.x < 0 or b.y < 0:
            b = Coordinate(b.x if b.x > 0 else 0, b.y if b.y > 0 else 0)
        ret = func(a, b)
        if ret.x < 0 or ret.y < 0:
            ret = Coordinate(ret.x if ret.x > 0 else 0, ret.y if ret.y > 0 else 0)
        return ret
    return checker

add = wrapper(add)
sub = wrapper(sub)

print sub(one, two)
print add(one, three)

@wrapper
def add1(a, b):
        return Coordinate(a.x + b.x, a.y + b.y)

@wrapper
def sub1(a, b):
        return Coordinate(a.x - b.x, a.y - b.y)

print sub1(one, two)
print add1(one, three)


def one(*args):
    print args # 1

one()
one(1, 2, 3)
def two(x, y, *args): # 2
    print x, y, args
two('a', 'b', 'c')


def logger(func):
    def inner(*args, **kwargs): #1
        print "Arguments were: %s, %s" % (args, kwargs)
        return func(*args, **kwargs) #2
    return inner


def foo(**kwargs):
    print kwargs
foo()
foo(x=1, y=2)

dct = {'x': 1, 'y': 2}
def bar(x, y):
    return x + y
print bar(**dct)

@logger
def foo1(x, y=1):
    return x * y

@logger
def foo2():
    return 2

foo1(5, 4)
foo1(x=5, y=4)
foo1(5, y=4)
foo1(1)
foo2()
