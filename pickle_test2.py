#coding=utf-8
import pickle, StringIO
  
class Person(object):
    '''自定义类型。
    '''
    def __init__(self, name, address):
        self.name = name
        self.address = address
     
    def display(self):
        print 'name:', self.name, 'address:', self.address 
         
fle = StringIO.StringIO()
pick = pickle.Pickler(fle)
person = Person("JGood", "Hangzhou China") 
  
pick.dump(person)
val1 = fle.getvalue()
print len(val1)
  
pick.clear_memo()    #注释此句，再看看运行结果
  
pick.dump(person)   #对同一引用对象再次进行序列化
val2 = fle.getvalue()
print len(val2)
  
#---- 结果 ----
#148
#296
#
#将这行代码注释掉：pick.clear_memo()
#结果为：
#148
#152

fle.seek(0)
unpick = pickle.Unpickler(fle)
person1 = unpick.load()
person1.display()
