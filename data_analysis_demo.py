#!/usr/bin/python

import pandas as pd
import matplotlib.pyplot as plt

#from http://python.jobbole.com/81133/

# Reading data locally
df = pd.read_csv('data.csv')
  
# Reading data from web
#data_url = "https://raw.githubusercontent.com/alstat/Analysis-with-Programming/master/2014/Python/Numerical-Descriptions-of-the-Data/data.csv"
#df = pd.read_csv(data_url)

print df.head()
print df.tail()
print df.columns
print df.index
print df.T
print df.ix[:, 0].head()
print df.ix[10:20, 0:3]
print df.drop(df.columns[[1, 2]], axis = 1).head()
print df.describe()

plt.show(df.plot(kind = 'box'))
