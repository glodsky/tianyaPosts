# -*- coding: cp936 -*-

import requests
from bs4 import BeautifulSoup
import re
import os
from hashlib import md5
from requests.exceptions import RequestException
from multiprocessing import Pool
from urllib import urlencode
from urllib import urlopen
from bs4 import BeautifulSoup
import json
import time
from lxml import etree
import lxml.etree as ET
import MySQLdb
import random

postitem =[]     
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    } 

def get_main_posts(hostid):
        result1 = 0
        url = "http://www.tianya.cn/api/bbsuser?var=bbsUser&method=userinfo.ice.getUserTotalList&params.userId=%s&_=1541920939022"%hostid
        data = {}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:                
                var = (response.text)[13:]
                data = json.loads(var)["data"]["list"]
                for item in data:
                        #insert_data("tb_posts", item)
                        if (item['title'].encode('gbk').find("回复")>0):
                                continue
##                        if (item['title'].encode('gbk').find("经历")>0):
##                                continue
                        print item['title'],item['url']
                        get_oneSaid_AllPosts(item['url'],interrupt = 0)
                        print ">>>>>>>>>>>>>>>>>>>>>>>>\n"
 
 
def getUrl(url,index):
        part = url.rfind("-")
        ss = url[0:part] +'-'+ str(index) + ".shtml" 
        return ss

def get_oneSaid_AllPosts(url,interrupt = 0):
        endindexs = 0
        if (interrupt ==0 ):
                response = requests.get(url,headers=headers)
                print "Handing %s"%str(1)
                interrupt = 1
                if response.status_code == 200:
                        html = ET.HTML(response.content)
                        handlepage(html,True)
                        print "Handling %s Over !\n"%str(1)
                        reval = html.xpath('//*[@id="post_head"]/div[3]/div[2]/form/a[4]/text()')
                        endindexs = int(reval[0])
        for index in range(interrupt,endindexs):                        
                nextUrl = getUrl(url,index) 
                print "Handling %s  %s " %(str(index),nextUrl)
                response = requests.get(nextUrl,headers=headers)
                html = ET.HTML(response.content)
                handlepage(html,False)
                print "Handled over  %s  %s \n" %(str(index),nextUrl)
                if( index % 30 == 0 ):
                        timenum = random.randint(1,5)
                        print "Random sleep %s"% timenum
                        time.sleep(timenum)
                      
 
def handlepage(html,maindiv = False):
        conn =  MySQLdb.connect(host="localhost", user="root", passwd="root", db="db_dao",charset='gbk')
        cursor = conn.cursor()
        if (maindiv == True):
                div0 = html.xpath('//*[@id="bd"]/div[4]/div[1]/div/div[2]/div[1]/text()')
                posts = div0[0].replace('|','').replace('\t','').replace('\n','').replace('\r','').replace('\\','').replace('\'','').replace('\/','').strip(' ')
                if (len(posts)>0): 
                        sql = """ insert into tb_items (bbs_content) values ( '%s' ) """ %  posts 
                        print sql                        
                        cursor.execute(sql)
                        conn.commit()                

        div1 = html.xpath('//div[@_hostid="55906926"]/div[2]/div/div[@class="bbs-content"]/text()')         
        for x1 in div1: 
                posts = x1.replace('|','').replace('\t','').replace('\n','').replace('\r','').replace('\\','').replace('\'','').replace('\/','').strip(' ')
                if not(len(posts)>0):
                        continue
                sql = """ insert into tb_items (bbs_content) values ( '%s' ) """ %  posts 
                print sql                        
                cursor.execute(sql)
                conn.commit()
        cursor.close()

        
def insert_data(dbName,data_dict):
    try:
        data_values = "( " + "%s," * (len(data_dict)) + ")"
        data_values = data_values.replace(',)', ')')
        dbField = data_dict.keys()
        dataTuple = tuple(data_dict.values())
        dbField = str(tuple(dbField)).replace("u'","'")
        dbField = dbField.replace("'"," ") 
        conn =  MySQLdb.connect(host="localhost", user="root", passwd="root", db="db_dao",charset='gbk')
        cursor = conn.cursor()
        sql = """ insert into %s  %s  values %s """ % (dbName,dbField,data_values)
        params = dataTuple
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        print "=====  插入成功  ====="
        return 1
    except Exception as e:
        print "********  插入失败    ********"
        print e
        return 0                            
        
#hostids = 55906926  用户
get_main_posts(55906926)
