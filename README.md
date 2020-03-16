# 使用 Docker 建置 PTT 爬蟲

### 使用工具說明：

  - Mac Pro 
  - Docker
  - MongoDB
  - Python
  - Visual Studio Code


### 安裝說明：

1. 安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 安裝完成後於終端機進行映像檔安裝，需要安裝的項目有：
    - mongodb(使用官方的image)
    - python(使用官方的image修改後建立自己的image)
安裝指令如下：
```sh
$ docker pull mongo
$ docker pull python
```

將github上的檔案全部下載到本機電腦後到工作目錄下建立自己的python image
例如將所有檔案下載放到/Users/使用者名字/Downloads，當執行以下建立自己的image指令時要確保工作目錄是在/Users/使用者名字/Downloads

編輯 DockerFile 設定好即將建立的image，內容如下：
```docker
### 設定使用官方的Python環境
FROM python
### 設定工作目錄
WORKDIR /app
### 將本機上的requirements.txt複製到容器裡面
COPY requirements.txt ./
### 安裝需要的Python套件的指令
RUN pip install --no-cache-dir -r requirements.txt
### 將本機上其他.py檔案等複製到容器裡面
COPY . /app
### 打開容器的5000端口
EXPOSE 5000
### 執行app.py檔案
CMD python3 app.py
```

編輯 requirements.txt 將需要使用的套件以及版本加入，內容如下：
```txt
appdirs==1.4.3
astroid==2.3.3
beautifulsoup4==4.8.2
bs4==0.0.1
certifi==2019.11.28
chardet==3.0.4
click==7.1.1
cssselect==1.1.0
dnspython==1.16.0
fake-useragent==0.1.11
Flask==1.1.1
idna==2.9
isort==4.3.21
itsdangerous==1.1.0
Jinja2==2.11.1
lazy-object-proxy==1.4.3
lxml==4.5.0
MarkupSafe==1.1.1
mccabe==0.6.1
parse==1.15.0
protobuf==3.6.1
pyee==7.0.1
pylint==2.4.4
pymongo==3.10.1
pyppeteer==0.0.25
pyquery==1.4.1
requests==2.23.0
requests-html==0.10.0
six==1.14.0
soupsieve==2.0
tqdm==4.43.0
typed-ast==1.4.1
urllib3==1.25.8
w3lib==1.21.0
websockets==8.1
Werkzeug==1.0.0
wrapt==1.11.2

```

編輯 post_title.py 將擷取每一頁文章列表的function寫在裡面，內容如下：
```Python
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

```

編輯 post.py 將擷取每一篇文章內容的function寫在裡面，內容如下：
```Python
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

```

編輯 index.html 將其放入 templates 資料夾裡面，才能讓 app.py 在返回首頁畫面時讀取到頁面，內容如下：
```html
<h1>您好，我是爬蟲！</h1>

<h3>抓取文章列表說明：</h3>
<p>網址後面加上post_title以及參數。</p>
<p>參數有startnum（開始頁碼）、stopnum（結束頁碼）、board（看板）</p>
<p>抓取電影看板第1～2頁範例：127.0.0.1:5000/post_title?startnum=1&stopnum=2&board=movie</p>

<h3>抓取文章頁面資訊說明：</h3>
<p>網址後面加上posts以及參數。</p>
<p>參數有startnum（開始文章編號）、stopnum（結束文章編號）</p>
<p>抓取文章編號第1～2範例：127.0.0.1:5000/posts?startnum=1&stopnum=2</p>

```

所有文件編輯完成後使用Docker指令將image打包建立，指令如下：
```Docker
$ docker build -t ptt-python .
```

映像檔建立完成後查看是否有兩個image已經建立，指令如下：
```Docker
$ docker images
```

確定映像檔建立完成後要透過映像檔建立容器，建立的同時會需要設定開啟容器對本機的端口，才能確定容器開啟後有達到需求（資料庫需要開啟的端口為27017、Python需要開啟的端口為5000），指令如下：
```Docker
$ docker run -p 27017:27017 mongo
$ docker run -p 5000:5000 ptt-python
```

可以透過 Docker Desktop 看到容器已經在執行中，也可以透過瀏覽器輸入網址查看是否有連線到
1. mongodb網址輸入：localhost:27017
2. Python網址輸入：localhost:5000

但容器之間的端口是沒有通的需要將兩個容器連接到同一個網路並且查看IP否則python會無法連線到資料庫會產生錯誤，範例指令如下：
```Docker
$ docker network create myNetwork
$ docker network connect myNetwork container1
$ docker network connect myNetwork container2
```

連接後可以在本機透過瀏覽器測試爬蟲是否運行成功。
