# -*- coding: utf-8 -*-
"""
Created on Sun May  8 20:27:58 2022

@author: user
"""

import requests #引入函式庫
import numpy as np
import re
import pandas as pd
import dash


from dash import html 
from dash import dcc
import flask
import os
from bs4 import BeautifulSoup
from dash.dependencies import Input, Output
import plotly.express as px
import csv

def RemoveHeaderSpace(_str):
    count = 0
    for idx, _s in enumerate(_str):
        
        if(_s == ' '):
            count+=1
        else:
            break
    return _str[count:]

def GetModelAndPrice(url):
    _model = []
    _price = []
    
    req = requests.get(url, headers = headers)
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, 'html.parser')
        # print(r2.text)
        Car_model1 = soup.select('li > a.brand-list-type')
        price = soup.find_all('div',class_='brand-list-price')
        
        for m,p in zip(Car_model1,price): #文字&特殊符號處理
            # print(m.text)
            # print(p.text)
            _model.append(m.text)
            Price1 = re.sub(r'\n| ', '', p.text)
            Price1 = re.sub(r'\t| ', '', Price1)
            
            if(Price1=='停售' or Price1=='暫無報價' or Price1=='未上市'):
                _pric = 0
            else:
                _pri = re.sub('萬', '', Price1)
                if('-' in _pri):
                    _pri = re.split('-', _pri)
                    _pric = (float(_pri[0]) + float(_pri[1]))/2
                else:
                    _pric = _pri
            
            _price.append(float(_pric))
            
    return _model, _price, soup

url ='https://c.8891.com.tw/Models'
headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"}

Car = []
count = 0 

r = requests.get(url, headers = headers)
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    # print(r.text)
    title = soup.select('li.gl-i > a')
    price = soup.select('div.brand-list-main IndexKindContent')
    
    for idx, t in enumerate(title):
        # 移除\n
        _txt = re.sub(r'\n', '', t.text)
        # 移除空白
        _txt = RemoveHeaderSpace(_txt)
        _txt = re.sub(r' ', '-', _txt)
        Car1 = re.split(r'\(', _txt)[0]
        Car1 = re.split(r'/', Car1)[0]
        Car.append(Car1)  
        print(Car1)
     
Car.sort()

Car_model = []
Price = []
for i in range(len(Car)):
    # Get one page information
    __model, __price, _soup = GetModelAndPrice('https://c.8891.com.tw/Models/'+str(Car[i]))
    print(Car[i])
    # print('page 1')
    # print(__model)
    # print(__price)
    
    next_page = _soup.find_all('div', class_='pagination default')
    
    if '共' in str(next_page):
        __model2, __price2, _soup2 = GetModelAndPrice('https://c.8891.com.tw/Models/'+str(Car[i])+'?page=2')
        # print(f'page 2')
        # print(__model2)
        # print(__price2)
        # print()
          
        Car_model.append(__model + __model2)
        Price.append(__price + __price2)  
    #     print(Car_model)
    #     print(Price)
    else:
        Car_model.append(__model)
        Price.append(__price)  
        
        
data = []
for i in range(len(Car)):
    for j in range(len(Car_model[i])):
        car_name = Car[i]
        model_name = Car_model[i][j]
        price_value = Price[i][j]
        _data = [car_name, model_name, price_value]
        data.append((_data))
        
# data.sort()
data = np.array(data)
# print(data)

with open('output.csv', 'w', newline='',encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    
    for i in data:
        writer.writerow(i)


server = flask.Flask('app')
server.secret_key = os.environ.get('secret_key', 'secret')

df = pd.read_csv('output.csv', header=None ,engine = "python")
# df = pd.DataFrame(data)
df.columns = ["Car", "Car_model", "Price(萬)"]

app = dash.Dash('app', server=server)

app.scripts.config.serve_locally = False

app.layout = html.Div([
    html.H1('Car Price'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[{'label': val, 'value': val} for val in Car],

        value='Audi'
    ),
    dcc.Graph(id='my-graph')
], className="container")


@app.callback(
    Output("my-graph", "figure"), 
    Input("my-dropdown", "value"))
def update_bar_chart(selected_dropdown_value):

    mask = df['Car'] == selected_dropdown_value
    fig = px.bar(df[mask], x="Car_model", y="Price(萬)")

    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
