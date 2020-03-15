import requests
from requests_html import HTML
import re
import urllib
import pymongo

# function 設定文章列表資訊的寬度
widths = [
        (126,    1), (159,    0), (687,     1), (710,   0), (711,   1),
        (727,    0), (733,    1), (879,     0), (1154,  1), (1161,  0),
        (4347,   1), (4447,   2), (7467,    1), (7521,  0), (8369,  1),
        (8426,   0), (9000,   1), (9002,    2), (11021, 1), (12350, 2),
        (12351,  1), (12438,  2), (12442,   0), (19893, 2), (19967, 1),
        (55203,  2), (63743,  1), (64106,   2), (65039, 1), (65059, 0),
        (65131,  2), (65279,  1), (65376,   2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
]

# function 設定文章標題的寬度
def calc_len(string):
    def chr_width(o):
        global widths
        if o == 0xe or o == 0xf:
            return 0
        for num, wid in widths:
            if o <= num:
                return wid
        return 1
    return sum(chr_width(ord(c)) for c in string)

# function 設定抓取文章列表資料顯示在終端機的寬度
def pretty_print(push, title, date, author):
    pattern = '%3s\t%s%s%s\t%s'
    padding = ' ' * (50 - calc_len(title))
    print(pattern % (push, title, padding, date, author))

# step-1 function 發送已滿18歲請求
def fetch(url):
    response = requests.get(url)
    response = requests.get(url, cookies={'over18': '1'})  # 一直向 server 回答滿 18 歲了 !
    return response

# step-2 function 回傳網頁HTML
def parse_article_entries(doc):
    html = HTML(html=doc)
    post_entries = html.find('div.r-ent')
    return post_entries

# step-3 function 解析整理資訊
def parse_article_meta(ent):
    ''' Step-3 (revised): parse the metadata in article entry '''
    # 基本要素都還在
    meta = {
        'title': ent.find('div.title', first=True).text,
        'push': ent.find('div.nrec', first=True).text,
        'date': ent.find('div.date', first=True).text,
    }

    try:
        # 正常狀況取得資料
        meta['author'] = ent.find('div.author', first=True).text
        meta['link'] = ent.find('div.title > a', first=True).attrs['href']
    except AttributeError:
        # 但碰上文章被刪除時，就沒有辦法像原本的方法取得 作者 跟 連結
        if '(本文已被刪除)' in meta['title']:
            # e.g., "(本文已被刪除) [haudai]"
            match_author = re.search('\[(\w*)\]', meta['title'])
            if match_author:
                meta['author'] = match_author.group(1)
        elif re.search('已被\w*刪除', meta['title']):
            # e.g., "(已被cappa刪除) <edisonchu> op"
            match_author = re.search('\<(\w*)\>', meta['title'])
            if match_author:
                meta['author'] = match_author.group(1)
    return meta

# step-4 function 整頁資訊放入list
def get_metadata_from(url):

    resp = fetch(url)
    post_entries = parse_article_entries(resp.text)

    metadata = [parse_article_meta(entry) for entry in post_entries]
    return metadata

# step-5 function 將資訊放入mongodb
def insert_metadata_mongodb(url):
    
    myclient = pymongo.MongoClient("mongodb://172.19.0.2:27017/")
    mydb = myclient["runoobdb"]
    mycol = mydb["post_title"]

    mylist = get_metadata_from(url)
    mycol.insert_many(mylist)

    for meta in mylist:
        pretty_print(meta['push'], meta['title'], meta['date'], meta['author'])
    

'''
for num in range(1,3,1):
    print('Now page ' + str(num) + ' : ')
    url = 'https://www.ptt.cc/bbs/movie/index'+ str(num) +'.html'
    insert_metadata_mongodb(url)
'''    



