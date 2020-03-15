from flask import Flask, request
import post_title
import posts
from flask import render_template

myclient = posts.pymongo.MongoClient("mongodb://172.19.0.2:27017/")
mydb = myclient["runoobdb"]
mycol = mydb["post_title"]
domain = 'https://www.ptt.cc'
app = Flask(__name__)


@app.route('/')
def index():

    return render_template('index.html')

@app.route('/post_title', methods=['GET'])
def for_post_title():
    startnum = request.args.get('startnum')
    stopnum = request.args.get('stopnum')
    board = request.args.get('board')

    for num in range(int(startnum),int(stopnum),1):
        print('Now page ' + str(num) + ' : ')
        url = 'https://www.ptt.cc/bbs/' + str(board) + '/index'+ str(num) +'.html'
        post_title.insert_metadata_mongodb(url)

    return render_template('index.html')

@app.route('/posts', methods=['GET'])
def for_posts():
    startnum = request.args.get('startnum')
    stopnum = request.args.get('stopnum')

    num = int(startnum)
    for x in mycol.find({},{ "_id": 0, "title": 1 , "author": 1 , "link": 1 }):
        print('Now Post No.' + str(num) + str(x['title']) + '......')
        url = domain + str(x['link'])
        authorID = str(x['author'])
        col_num = str(num)
        posts.insert_metadata_mongodb(url,authorID,col_num)
        posts.time.sleep(2.5)
        if(num % 10 == 0):
            posts.time.sleep(5)
        num = num + 1

        if (num == int(stopnum)):
            break

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)