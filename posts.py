import requests
from requests_html import HTML
import re
import pymongo
import time
 
'''
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["runoobdb"]
mycol = mydb["post_title"]
domain = 'https://www.ptt.cc'
'''


# function 發送已滿18歲請求
def fetch(url):
    response = requests.get(url)
    response = requests.get(url, cookies={'over18': '1'})  # 一直向 server 回答滿 18 歲了 !
    return response

# function 回傳網頁標題HTML
def parse_title_entries(doc):
    html = HTML(html=doc)
    title_entries = html.find('div.article-metaline')
    author = title_entries[0].find('span.article-meta-value',first=True).text
    title = title_entries[1].find('span.article-meta-value',first=True).text
    createdTime = title_entries[2].find('span.article-meta-value',first=True).text
    return author, title, createdTime

# function 回傳網頁文章
def parse_post_entries(doc):
    html = HTML(html=doc)
    post_entries = html.find('#main-content',first=True).text
    post_content = post_entries.split('※ 發信站: 批踢踢實業坊(ptt.cc)')[0]
    post_content = post_content.split('\n')
    if (len(post_content) == 5):
        content = post_content[4]
    else:
        content = post_content[5]

    return content

# function 回傳網頁留言HTML
def parse_comment_entries(doc):
    html = HTML(html=doc)
    comment_entries = html.find('div.push')
    
    return comment_entries

# function 解析整理資訊
def parse_article_meta(authorID,author,title,url,createdTime,content,ent):
    
    meta = {
        'authorID': authorID,
        'authorName': author,
        'title': title,
        'content': content,
        'canonicalUrl': url,
        'createdTime': createdTime,
        'updateTime': createdTime,
        'commentID': ent.find('span.push-userid',first=True).text,
        'commentContent': ent.find('span.push-content',first=True).text,
        'commentTime': ent.find('span.push-ipdatetime',first=True).text,
        'push': ent.find('span.push-tag',first=True).text
    }
    return meta

# function 整頁資訊放入list
def get_metadata_from(url,authorID):

    resp = fetch(url)
    author, title, createdTime = parse_title_entries(resp.text)
    content = parse_post_entries(resp.text)
    comment_entries = parse_comment_entries(resp.text)

    metadata = [parse_article_meta(authorID,author,title,url,createdTime,content,entry) for entry in comment_entries]

    return metadata

# function 將資訊放入mongodb
def insert_metadata_mongodb(url,authorID,col_num):
    
    myclient = pymongo.MongoClient("mongodb://172.19.0.2:27017/")
    mydb = myclient["runoobdb"]
    mycol = mydb["post" + col_num]

    try:
        mylist = get_metadata_from(url,authorID)
        mycol.insert_many(mylist)
    except:
        print("Something went wrong (maybe 404)")
    else:
        print("Nothing went wrong")

'''
# 查詢集合中所有資料並且新增
num = 1
for x in mycol.find({},{ "_id": 0, "title": 1 , "author": 1 , "link": 1 }):
    print('Now Post No.' + str(num) + str(x['title']) + '......')
    url = domain + str(x['link'])
    authorID = str(x['author'])
    col_num = str(num)
    insert_metadata_mongodb(url,authorID,col_num)
    time.sleep(1)
    num = num + 1
'''

