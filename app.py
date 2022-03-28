# import module
from flask import Flask, render_template
from flask import Response, request, redirect, url_for
from flask import send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.utils import secure_filename

import os

import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import japanize_matplotlib
import time
import datetime
import re


# flask incetance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    keyword = db.Column(db.String(50), nullable=False)


@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        # GETでアクセスされた時、searchを表示
        return render_template('search.html')
    else:
        url = request.form.get('url')
        keyword = request.form.get('keyword')
        new_post = Post(keyword=keyword, url=url)

        db.session.add(new_post)
        db.session.commit()

        #今日の日付を取得
        #today = datetime.datetime.now()
        #today_now = today.strftime('%y%m%d%H')
        #return '<h1>Hello World</h1>'
        

        class Search:
            def __init__(self, url):
                self.url = url

        #データを取得する関数
            def search(self, url):
                url=self.url          
                html=requests.get(url)
                soup=BeautifulSoup(html.text,'html.parser')
                info=soup.select('._2W0PXaK-syIW')

                return info



        def research(items, url): ##URL
            df = []
            rank=1

            for item in items:
                title = item.select_one('._2EW-04-9Eayr').text.replace('\n','')
                shopname = item.select_one('._2RweXo29absZ').text.replace('\n','')
                price=item.select_one('._3-CgJZLU91dR').text.replace('\n','').replace(' ','')

                if item.select_one('.Review__average') != None:
                    review = item.select_one('.Review__average').text.replace('\n','')
                    rev_cn = item.select_one('.Review__count').text.replace('\n','')
                    #数字抽出のため正規化
                    rev_cn = re.search(r'(\d+)', rev_cn)
                    rev_cn = rev_cn.group()
                else:
                    review = '0'
                    rev_cn = '0'

                #print('レビュー：{}'.format(review))
                
                ddf = [rank,shopname,title,price,review, rev_cn]
                df.append(ddf)
                df1 = pd.DataFrame(data = df, columns=['順位','ショップ名', '商品名', '価格', 'レビュー', '件数'])
                rank+=1

            print(df1)
            #df1.to_csv(today.strftime('%y_%m_%d') + ".csv", encoding='utf_8_sig', index=False)
            return df1

        #ページの情報を格納
        def output(x):
            S = Search(x)
            items = S.search(x)
            df1 = research(items, x)

            return df1

        df1 = output(url)


        #API活用したデータの取得==============================================================
        REQUEST_URL = "URL"
        APP_ID = "API"
        # 入力パラメータ
        search_keyword = keyword ##キーワード


        # 商品情報をリストで取得
        item_list = [] # 30件ずつ取得した辞書型の商品情報tmp_itemがmax_pageページ分入る
        item_list_2 = []
        item_list_3 = []

        tmp_item = {}
        tmp_item_2 = {}
        tmp_item_3 = {}

        page = 4

        for i in range(1,page+1):
            search_params = {
                'appid': APP_ID,
                'query':search_keyword,
                'period':'weekly',
                'start':1 + 100*(i-1),
                'in_stock':'true',
                'results':100*1,
                'sort':'-score'
            }

            # APIにリクエストを送り、結果として商品データresultを得る
            response = requests.get(REQUEST_URL, search_params)
            result = response.json()


            for i in range(result['totalResultsReturned']):
            
                item_key = ['name', 'description', 'headLine', 'price', 'url', 'code']

                tmp_item = {}
                item = result['hits'][i]

                # for文を回してdictを作る
                for key, value in item.items():
                    if key in item_key:
                        tmp_item[key] = value            
                item_list.append(tmp_item.copy())

                item_key_2 = ['rate']

                tmp_item_2 = {}
                item_2 = result['hits'][i]['review']

                # for文を回してdictを作る
                for key, value in item_2.items():
                    if key in item_key_2:
                        tmp_item_2[key] = value
                item_list_2.append(tmp_item_2.copy())

                item_key_3 = ['name', 'url']
                tmp_item_3 = {}
                item_3 = result['hits'][i]['seller']

                # for文を回してdictを作る
                for key, value in item_3.items():
                    if key in item_key_3:
                        tmp_item_3[key] = value
                item_list_3.append(tmp_item_3.copy())

        # データフレームを作成
        hits = pd.DataFrame(item_list)
        hits.columns=['商品名', '商品説明', 'キャッチコピー', '商品URL', '商品コード', '価格']

        rev = pd.DataFrame(item_list_2)
        rev.columns = ['レビュー']
        rev['レビュー'] = rev['レビュー'].astype(str)

        sell = pd.DataFrame(item_list_3)
        sell.columns = ['店舗名', '店舗URL']


        api = pd.concat([hits, rev, sell], axis = 1)

        Yah = df1

        ret = pd.merge(Yah, api, on=['商品名', 'レビュー'])
        ret.to_csv('./results/result.csv', encoding='utf_8_sig', index=False)
        print(ret)
        #キーワードがサーバに保存されたらdownloadsに遷移
        return render_template('download.html')

@app.route("/download")
def download():
    file_path = './results/result.csv'
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug = True)
    app.run()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
