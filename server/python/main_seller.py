from flask import Flask, request, make_response
from flask_cors import CORS, cross_origin
from flask_mysqldb import MySQL
from flask_limiter import Limiter, util
from datetime import datetime, timedelta
# from jwt import algorithms, ExpiredSignatureError, decode
from functools import wraps
from MySQLdb import OperationalError
import MySQLdb.cursors as curdict
import pandas as pd
import uuid
import boto3
import base64

application = app = Flask(__name__)
cros = CORS(app)

limiter = Limiter(
    application,
    key_func=util.get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MYSQL_HOST'] = 'projects.cbcvudzl6rdd.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'DarkShadow2806'
app.config['MYSQL_DB'] = 'ecommerce'
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = '0898a671f37849d79ed8126dd469dcd1'

app.mysql = MySQL(app)


@app.get('/')
def home():
    return make_response({'message': 'Home'})


@app.post('/register')
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    cur = app.mysql.connection.cursor()
    cur.execute(
        "INSERT INTO seller (seller_name, seller_id) VALUES (%s, %s)", (name, email))
    app.mysql.connection.commit()
    cur.close()
    return make_response({'message': 'User created'})


@app.get('/orders')
def orders_get():
    try:
        app.mysql.connection.commit()
    except OperationalError as SQLdbError:
        if "Lost connection" not in str(SQLdbError):
            return SQLdbError.__dict__
        app.mysql.connection = MySQL(app)
    seller_id = request.args.get('seller_id')
    cur = app.mysql.connection.cursor(curdict.DictCursor)
    cur.execute(
        "SELECT * from orders join products_in_order using(order_no) join products using(sku) where seller_id = %s", (seller_id,))
    data = cur.fetchall()
    cur.close()
    if data:
        for i in data:
            i['Images'] = eval(i['Images'])
        return make_response({'data': data}), 200
    else:
        return make_response({'message': 'No orders'}), 404


@app.put('/order')
def order_put():
    data = request.get_json()
    order_id = data['order_id']
    status = data['status']
    try:
        app.mysql.connection.commit()
    except OperationalError as SQLdbError:
        if "Lost connection" not in str(SQLdbError):
            return SQLdbError.__dict__
        app.mysql.connection = MySQL(app)
    cur = app.mysql.connection.cursor(curdict.DictCursor)
    cur.execute('UPDATE orders SET status = %s WHERE order_no = %s',
                (status, order_id))
    app.mysql.connection.commit()
    cur.close()
    return make_response({'message': 'Updated order status'}), 200


@app.post('/add_product')
def add_product():
    data = request.get_json()
    sku = data['sku']
    name = data['name']
    reg_price = data['reg_price']
    seller_id = data['seller_id']
    category = data['category']
    description = data['description']
    images = data['images']
    inventory = data['inventory']
    keywords = data['keywords']
    image_urls = []
    s3 = boto3.client('s3')
    for i in range(len(images)):
        s3.put_object(
            Key=f'images/{sku}_{i+1}.png', Body=base64.b64decode(bytes(images[i], 'utf-8')), Bucket='ecommercecloneproductimages')
        image_urls.append(
            f'https://ecommercecloneproductimages.s3.amazonaws.com/images/{sku+f"_{i+1}.png"}')
    try:
        app.mysql.connection.commit()
    except OperationalError as SQLdbError:
        if "Lost connection" not in str(SQLdbError):
            return SQLdbError.__dict__
        app.mysql.connection = MySQL(app)
    if not sku or not name or not reg_price or not seller_id or not category or not description or not images or not inventory or not keywords:
        return make_response({'message': 'Missing data'}), 400
    else:
        try:
            cur = app.mysql.connection.cursor(curdict.DictCursor)
            cur.execute("INSERT INTO products(`SKU`, `Title`,`Description`,`Images`,`Reg_price`,`Inventory`,`seller_id`,`category`) VALUES('%s', '%s', '%s', '%s', % s, % s, '%s', '%s')" % (
                sku, name, description, str(image_urls).replace("'", '"'), reg_price, inventory, seller_id, category))
            app.mysql.connection.commit()
            if keywords:
                keywords = keywords.split(',')
                for keyword in keywords:
                    cur.execute("INSERT INTO keywords VALUES ('%s','%s')" %
                                (keyword, sku))
                    app.mysql.connection.commit()
            cur.close()
            return make_response({'message': 'Product added'}), 200
        except OperationalError as SQLdbError:
            if "Duplicate entry" in str(SQLdbError):
                return make_response({'message': 'Product already exists'}), 400
            else:
                return make_response({'message': str(SQLdbError.__dict__)}), 400


@app.get('/categories')
def categories_get():
    try:
        app.mysql.connection.commit()
    except OperationalError as SQLdbError:
        if "Lost connection" not in str(SQLdbError):
            return SQLdbError.__dict__
        app.mysql.connection = MySQL(app)
    cur = app.mysql.connection.cursor(curdict.DictCursor)
    cur.execute("SELECT * from categories")
    data = cur.fetchall()
    app.mysql.connection.commit()
    cur.close()
    return make_response({'data': data}), 200


@app.get('/products')
def products_get():
    try:
        app.mysql.connection.commit()
    except OperationalError as SQLdbError:
        if "Lost connection" not in str(SQLdbError):
            return SQLdbError.__dict__
        app.mysql.connection = MySQL(app)
    cur = app.mysql.connection.cursor(curdict.DictCursor)
    query = "SELECT * from products where seller_id=%s"
    arguments = (str(request.args.get('seller_id')),)
    cur.execute(query, arguments)
    data = cur.fetchall()
    # app.mysql.connection.commit()
    cur.close()
    for i in data:
        i['Images'] = eval(i['Images'])
    return make_response({'data': data}), 200


@app.delete('/product')
def delete_product():
    try:
        sku = request.args.get('sku')
        cur = app.mysql.connection.cursor(curdict.DictCursor)
        cur.execute("DELETE FROM products WHERE SKU='%s'" % (sku))
        app.mysql.connection.commit()
        cur.close()
        return make_response({'message': 'Product deleted'}), 200
    except OperationalError as SQLdbError:
        return make_response({'message': str(SQLdbError)}), 400


@app.get('/earnings')
def earnings_get():
    try:
        seller_id = request.args.get('seller_id')
        cur = app.mysql.connection.cursor(curdict.DictCursor)
        cur.execute("with a as (select * from categories),\
                    b as (select category, sum(p.reg_price*po.quantity) as total from products_in_order po join products p using(sku) where p.seller_id=%s)\
                    select a.category_name, b.total from a left join b on a.category_id=b.category", (seller_id,))
        data = cur.fetchall()
        cur.close()
        if data:
            for i in data:
                i['total'] = int(i['total']) if i['total'] else 0
            return make_response({'data': data}), 200
    except OperationalError as SQLdbError:
        return make_response({'message': str(SQLdbError)}), 400


@app.get('/routes')
def routes():
    routes = []
    for route in app.url_map.iter_rules():
        routes.append('%s' % route)
    return make_response({'routes': routes}), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5001)
