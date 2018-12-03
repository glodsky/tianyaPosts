# -*- coding: cp936 -*-

import requests
import re
import os
from hashlib import md5
from requests.exceptions import RequestException
import json
import time
from lxml import etree
import lxml.etree as ET
import sqlite3
import random

postitem =[]     
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    } 

def create_table(db_name):
    conn = sqlite3.connect(db_name)
    try:
        create_tb_cmd='''
        CREATE TABLE IF NOT EXISTS WB_CONTENT
        (wb_address TEXT,
        create_at CHAR(25),
        wb_detail TEXT,
        attitudes_count INT,
        comments_count INT,
        reposts_count INT       
        );
        '''
        conn.execute(create_tb_cmd)
    except:
        print( "Create table failed")
        return False 
    conn.commit()
    conn.close() 

def exists_in_db(data,db_name): #  (scheme ,str(created_at),text,attitudes_count,comments_count, reposts_count)
   (wb_address,create_at,wb_detail,attitudes_count,comments_count,reposts_count)=data
   sql = "select count(*)  from WB_CONTENT where create_at='%s' and   wb_detail='%s'  "%(create_at,wb_detail )
   conn = sqlite3.connect(db_name)
   c = conn.cursor()
   try:
       counts = 0 
       cursor = c.execute(sql)
       for row in cursor:
           counts = row[0]
           break
       if counts > 0 :
           conn.close()
           return True
       else:
           conn.close()
           return False
   except:
        print ("select table failed\n SQL:%s"%sql)
        conn.close()
        return False         
    
def insert_into_db(data,db_name):
    conn = sqlite3.connect(db_name)
    try:
        sql = "insert into WB_CONTENT values(?,?,?,?,?,?)"
        #print('执行sql:[{}],参数:[{}]'.format(sql, data))
        conn.execute(sql,data)
    except:
        print ("Insert table failed")
        return False 
    conn.commit()
    conn.close()
    
def get_main_posts(hostid):
        result1 = 0
        url = "http://www.tianya.cn/api/bbsuser?var=bbsUser&method=userinfo.ice.getUserTotalList&params.userId=%s&_=1541920939022"%hostid
        data = {}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:                
                var = (response.text)[13:]
                data = json.loads(var)["data"]["list"] 
                for item in data:
                        title = str(item['title'].encode('utf-8'))
                        url = item['url']
                        if url.find('?')>0 or title.find('回复') > 0 :
                                continue
##                        if title.find('[') < 0 : #仅爬取 [经历]
##                                continue
                        print( "%s  \n %s" %(item['title'],item['url']))
                        get_oneSaid_AllPosts(item['url'],interrupt =0) 
                        print( ">>>>>>>>>>>>>>>>>>>>>>>>\n")
 
 
def getUrl(url,index):
        part = url.rfind("-")
        ss = url[0:part] +'-'+ str(index) + ".shtml" 
        return ss
def get_EndIndexs(url):
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
                html = ET.HTML(response.content)
                reval = html.xpath('//*[@id="post_head"]/div[3]/div[2]/form/a[4]/text()')
                endindexs = int(reval[0])
                return endindexs
        else:
                return 0
                        
def get_oneSaid_AllPosts(url,interrupt = 0): # interrupt 在被服务器拒绝后 重新爬取时设置的起始位
        endindexs = 0
        if (interrupt ==0 ):
                response = requests.get(url,headers=headers)
                print( "Handing %s"%str(1))
                interrupt = 1
                if response.status_code == 200:
                        html = ET.HTML(response.content)
                        handlepage(html,url,True)
                        print( "Handling %s Over !\n"%str(1))
        endindexs = get_EndIndexs(url)
        if endindexs <=0 :
                return 
        for index in range(interrupt,endindexs):                        
                nextUrl = getUrl(url,index) 
                print( "Handling %s  %s " %(str(index),nextUrl))
                response = requests.get(nextUrl,headers=headers)
                html = ET.HTML(response.content)
                handlepage(html,url,False)
                print( "Handled over  %s  %s \n" %(str(index),nextUrl))
                if( index % 30 == 0 ):
                        timenum = random.randint(1,5)
                        print( "Random sleep %s"% timenum)
                        time.sleep(timenum)
                      
 
def handlepage(html,url,maindiv = False):
        wb_detail = ""
        if (maindiv == True):                
                div0 = html.xpath('//div[@_hostid="55906926"]/div/div/div[@class="bbs-content clearfix"]/text()')
                for ds in div0:
                        wb_detail= wb_detail + ds
                wb_detail=  wb_detail.replace('|','').replace('\t','').replace('\n','') \
                           .replace('\r','').replace('\\','').replace('\'','').replace('\"','').replace('\'','')  \
                           .replace('\/','').replace('\u3000','').strip(' ')
                wb_address = url
                create_at = (html.xpath('//*[@id="post_head"]/div[2]/div[2]/span[2]/text()')[0]).split('：')[1]
                attitudes_count = int( html.xpath('//div[@js_activityuserid="55906926"]/@js_clickcount')[0])
                reposts_count = int(html.xpath('//div[@js_activityuserid="55906926"]/@js_replycount')[0])
                comments_count = 0
                #print("%s  %s  %s  %s  %s  %s"%(wb_address,wb_detail,create_at,attitudes_count,comments_count,reposts_count))
                data = (wb_address,create_at,wb_detail,attitudes_count,comments_count,reposts_count)   
                if not exists_in_db(data,'data.db'):
                        insert_into_db(data,'data.db')
                        
        target_elist = html.xpath('//div[@_hostid="55906926"]/div[2]/div/div[@class="bbs-content"]')
        create_at_tlist = html.xpath('//div[@_hostid="55906926"]/div[1]/div/span[2]/text()')
        #print("%s  %s"%(len(target_elist) ,len(create_at_tlist)))
        wb_detail_el_count = len(target_elist)
        create_at_tl_count = len(create_at_tlist)
        if wb_detail_el_count ==0 or create_at_tl_count ==0 :
                return 
        if (wb_detail_el_count != create_at_tl_count):
                print("wb_detail_el_count and create_at_el_count is not equal\n")
                return
        wb_details = []
        for te in target_elist:
                dt_e_text = te.xpath('./text()')
                o_detail=""
                for cd1 in dt_e_text:
                        o_detail = o_detail + cd1
                o_detail=o_detail.replace('|','').replace('\t','').replace('\n','') \
                           .replace('\r','').replace('\\','').replace('\'','')  \
                           .replace('\/','').replace('\u3000','').strip(' ')
                wb_details.append(o_detail)
                        
        for x  in range(create_at_tl_count):
                wb_detail = wb_details[x]
                wb_address = url
                create_at =  create_at_tlist[x].split('：')[1]
                attitudes_count = 0
                reposts_count =  0
                comments_count = 0
                #print("%s  %s  %s  %s  %s  %s"%(wb_address,wb_detail,create_at,attitudes_count,comments_count,reposts_count))
                data = (wb_address,create_at,wb_detail,attitudes_count,comments_count,reposts_count)   
                if not exists_in_db(data,'data.db'):
                        insert_into_db(data,'data.db')        

create_table('data.db')
#hostids = 55906926
get_main_posts(55906926)
