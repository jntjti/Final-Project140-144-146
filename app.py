import os
from flask import Flask, request, jsonify, make_response, render_template, Blueprint
from flask_restx import Resource, Api
from PIL import Image
import json
import requests
from werkzeug import datastructures
from urllib.parse import quote
from urllib.request import urlopen
from ml_model import TFModel

APPKEY = "thisisapikey"

UPLOAD_FOLDER = './static/uploads'

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api = Api(app)


f = open('book.json', encoding="utf8")
book_data = json.load(f)
f.close()

model = TFModel(model_dir='./ml-model/')
model.load()


def delete():
    request.form.get("id")
    url = "http://127.0.0.1:5000/book/delete/{0}"
    id = request.form['id']
    req = url.format(id)
    requests.delete(req, headers={'X-AUTH-TOKEN':APPKEY})
    return render_template('delete.html')

@app.route('/bookpred', methods=['GET', 'POST']) #################### Machine Learing ###############
def upload_file():
    if request.method == 'POST':
        if 'file1' not in request.files:
            return 'there is no file1 in form!'
        file1 = request.files['file1']
        path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file1.save(path)

        image_1 = Image.open(path)
        outputs = model.predict(image_1)

        return render_template('prediction.html', pred_result=outputs)

    return render_template('upload.html') #########################################################

@app.route('/home', methods = ['GET', 'POST', 'DELETE'])
def home():
    req = "http://127.0.0.1:5000/book/all"
    if  request.method == 'GET':
        data = requests.get(req, headers={'X-AUTH-TOKEN':APPKEY}).json()
        return render_template('home.html', data=data)
    elif request.form.get("keyword"):
        keyword = request.form['keyword']
        req = "http://127.0.0.1:5000/book/{0}"
        req = req.format(keyword)
        data = requests.get(req, headers={'X-AUTH-TOKEN':APPKEY}).json()
        return render_template('home.html', data=data)
    elif request.form.get("id"):
        delurl = "http://127.0.0.1:5000/book/delete/{0}"
        id = request.form['id']
        delreq = delurl.format(id)
        requests.delete(delreq, headers={'X-AUTH-TOKEN':APPKEY})
        data = requests.get(req, headers={'X-AUTH-TOKEN':APPKEY}).json()
        return render_template('home.html', data=data)

@app.route('/create', methods = ['GET', 'POST'])
def create():
    url = "http://127.0.0.1:5000/book/create"
    if request.method == 'GET':
        return render_template('create.html')
    else:   
        data = {"id": request.form['id'],
                "title": request.form['title'], 
                "author": request.form['author'],
                "categories": request.form['categories'],
                "year":  request.form['year'],
                "page": request.form['page']
                }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(url, data=json.dumps(data), headers=headers)
    return render_template('create.html')

@app.route('/update', methods=['GET', 'POST'])
def update():
    url = "http://127.0.0.1:5000/book/update/{0}"   
    if request.method == 'GET':
        return render_template('update.html')
    else:
        book_id = request.form['id']
        url = url.format(book_id)
        data = {"id": book_id,
                "title": request.form['title'], 
                "author": request.form['author'],
                "categories":  request.form['categories'],
                "year": request.form['year'],
                "pages": request.form['pages']
                }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.put(url, data=json.dumps(data), headers=headers)
    return render_template('update.html')

@app.route('/about')
def about():
    return render_template('about.html')

class getBook(Resource): # เรียกข้อมูลหนังสือทั้งหมด
    def get(self):
        data = []
        for i in book_data['response']['books']:
            data.append(i)
        return data

class getBookid(Resource): # เรียกข้อมูลหนังสือจาก Keyword
    def get(self, id):
        data = []
        for i in book_data['response']['books']:
            if id.capitalize() in i['title']:
                data.append(i)
        return data

class postBook(Resource): # เพิ่มข้อมูลหนังสือ
    def post(self):
        book = {
            'id': api.payload['id'],
            'title': api.payload['title'],
            'author': api.payload['author'],
            'categories': api.payload['categories'],
            'year': api.payload['year'],
            'pages': api.payload['pages']
        }
        book_data['response']['books'].append(book)
        return api.payload, 201


class updateBook(Resource):
    def put(self, id):
        for i in range(len(book_data['response']['books'])):
            if book_data['response']['books'][i]['id'] == id:
                book_data['response']['books'][i]['id'] = request.json['id']
                book_data['response']['books'][i]['title'] = request.json['title']
                book_data['response']['books'][i]['author'] = request.json['author']
                book_data['response']['books'][i]['categories'] = request.json['categories']
                book_data['response']['books'][i]['year'] = request.json['year']
                book_data['response']['books'][i]['pages'] = request.json['pages']
                return book_data['response']['books'][i]



class deleteBook(Resource): # ลบหนังสือจาก เลือกจาก id หนังสือ
    def delete(self, id):
        for i in range(len(book_data['response']['books'])):
            if book_data['response']['books'][i]['id'] == id:
               del book_data['response']['books'][i]
               break
        return book_data['response']['books']


api.add_resource(getBook,'/book/all')
api.add_resource(getBookid,'/book/<string:id>')
api.add_resource(updateBook,'/book/update/<string:id>')
api.add_resource(postBook,'/book/create')
api.add_resource(deleteBook,'/book/delete/<string:id>')



