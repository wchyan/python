#!/usr/bin/python

import smtplib, mimetypes 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart  
from email.mime.image import MIMEImage 

mail_list = "mamh@marvell.com,wchyan@marvell.com"

msg = MIMEMultipart()  
msg['From'] = "Weichuan Yan <wchyan@marvell.com>" 
msg['To'] = 'mamh@marvell.com, wchyan@marvell.com' 
msg['Subject'] = 'Email for Tesing' 

txt = MIMEText("This message ...")
msg.attach(txt)

fileName = r'smtp_test.py' 
ctype, encoding = mimetypes.guess_type(fileName)  
print ctype, encoding

if ctype is None or encoding is not None:  
    ctype = 'application/octet-stream' 
maintype, subtype = ctype.split('/', 1)  
print maintype, subtype

att1 = MIMEImage((lambda f: (f.read(), f.close()))(open(fileName, 'rb'))[0], _subtype = subtype)  
att1.add_header('Content-Disposition', 'attachment', filename = fileName)  
msg.attach(att1)

to_who = [ x for x in mail_list.split(',')]
smtp = smtplib.SMTP("10.93.76.20")
smtp.sendmail(["wchyan@marvell.com"], to_who, msg.as_string())
smtp.quit()
