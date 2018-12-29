#!/usr/bin/python

import smtplib   
   
smtp = smtplib.SMTP()   
smtp.connect("smtp.163.com", "25")   
smtp.login('yanweichuan@163.com', 'xxx')
smtp.sendmail('yanweichuan@163.com', 'wchyan@marvell.com', 'From: from@yeah.net/r/nTo: to@21cn.com/r/nSubject: this is a email from python demo/r/n/r/nJust for test~_~')   
smtp.quit()
