from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from send import send_receipt, new_receipt, delete_automated_receipt, get_all_automated_receipts
from datetime import datetime
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_sqlalchemy import SQLAlchemy
import hashlib
import hmac
from Sellix import Sellix


# -----------------------------------
# -------------- FLASK --------------
# -----------------------------------

app = Flask(__name__)

app.secret_key = b'\x1c\xe1\xe7\x16Ja\xce\x889\x05\xcd\xcd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:vlad2306@localhost/fkdatabase'
db = SQLAlchemy(app)

app.app_context().push()

admin_username = "fklogin"
admin_passw = "Kapitan123*"
secret = "AD2583878CFD5"

# -------------------------------------
# --------------DATABASE---------------
# -------------------------------------

class SellixIds(db.Model):
    __table__ = db.Table('SellixIds', db.metadata, autoload_with=db.engine)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def create_row(cls, database_id, sellix_id):
        cls(database_id=database_id, sellix_id=sellix_id).save_to_db()

    @classmethod
    def get_sellix_id(cls, database_id):
        return cls.query.filter_by(database_id=database_id).first().sellix_id

class Affiliate(db.Model):
    __table__ = db.Table('affiliate', db.metadata, autoload_with=db.engine)


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class PromoCode(db.Model):
    __table__ = db.Table('promocodes', db.metadata, autoload_with=db.engine)
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_promocode(cls, code):
        return cls.query.filter_by(code=code).first()

    def increament_promo(self):
        self.timesUsed += 1
        db.session.commit()

    @classmethod
    def check_promo(cls, code):
        promo = cls.get_promocode(code)
        if promo != None:
            promo.increament_promo()
            return promo.discount
        else:
            return False

    @classmethod
    def delete_promo(cls, promo_id):
        if cls.query.filter_by(id=promo_id).first() != None:
            db.session.delete(cls.query.filter_by(id=promo_id).first())
            db.session.commit()
        else:
            pass

    @classmethod
    def save_promocode(cls, code, discount):
        cls(code=code, discount=discount, timesUsed=0).save_to_db()

    @classmethod
    def get_promocodes(cls):
        return [{"id":i.id,"code":i.code,"discount":i.discount, "timesUsed":i.timesUsed} for i in cls.query.all()]


class Order(db.Model):
    __table__ = db.Table('orders', db.metadata, autoload_with=db.engine)
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def mark_as_done(cls, orderid):
        order = cls.query.filter_by(orderId=orderid).first()
        order.status = 'DONE'
        db.session.commit()

    @classmethod
    def save_order(cls, orderid, orderinfo, status, order_date):
        status = "DONE" if status else "NOT DONE"
        orderContent = json.dumps(orderinfo)
        if orderid.endswith("addServ"):
            orderinfo['ordername'] = orderinfo['ordername'].replace("EMAIL", "PAPER") if 'EMAIL' in orderinfo[
                'ordername'] else orderinfo['ordername'].replace("PAPER", "EMAIL")
        cls(orderId=orderid, orderContent=orderContent, status=status, order_date=order_date, email=orderinfo['email'], order_name=orderinfo['ordername']).save_to_db()

    @classmethod
    def get_orders(cls, done=None, email=None):
        if done == None and email == None:
            response = cls.query.order_by(cls.order_date.desc()).all()
        elif done == False and email == None:
            response = cls.query.filter_by(status="NOT DONE").order_by(cls.order_date.desc()).all()
        elif done == None and email != None:
            response = cls.query.filter_by(email=email).order_by(cls.order_date.desc()).all()
        elif done == False and email != None:
            response = cls.query.filter_by(status="NOT DONE").filter_by(email=email).order_by(cls.order_date.desc()).all()
        return [{"orderId": i.orderId, "orderContent": i.orderContent, "status": i.status, "order_date": i.order_date, "email": i.email,
                 "order_name": i.order_name} for i in response]

    @classmethod
    def get_order(cls, orderid):
        order = cls.query.filter_by(orderId=orderid).first()
        if order == None:
            return order
        else:
            return {"orderId": order.orderId, "orderContent": order.orderContent, "status": order.status, "order_date": order.order_date,
                    "email": order.email, "order_name": order.order_name}

class Item(db.Model):
    __table__ = db.Table('items', db.metadata, autoload_with=db.engine)
    best_items = ['STOCKX EMAIL INVOICE', 'APPLE EMAIL INVOICE', 'GOAT EMAIL INVOICE', 'DIOR EMAIL INVOICE']

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def create_item(cls, requiredInfo, description, url, thumbnailUrl, itemName, type, price):
        if Question.questions_for_item(requiredInfo.split(',')) == None:
            raise Exception
        cls(requiredInfo=requiredInfo, description=description, url=url, thumbnailUrl=thumbnailUrl, itemName=itemName, type=type, price=price).save_to_db()

    @classmethod
    def delete_item(cls, itemid):
        if cls.query.filter_by(id=itemid).first() != None:
            db.session.delete(cls.query.filter_by(id=itemid).first())
            db.session.commit()
        else:
            raise Exception

    @classmethod
    def get_best_items(cls):
        return [{"thumbnailUrl": i.thumbnailUrl, "itemName": i.itemName, 'id': i.id, 'type': i.type} for i in cls.query.filter(cls.itemName.in_(cls.best_items)).all()]

    @classmethod
    def get_items(cls, item_type):
        if item_type == 'all':
            return [{"thumbnailUrl": i.thumbnailUrl, "itemName": i.itemName, 'id': i.id, 'type': i.type, 'url':i.url} for i in Item.query.all()]
        else:
            return [{"thumbnailUrl": i.thumbnailUrl, "itemName": i.itemName, 'id': i.id, 'type': i.type, "url":i.url} for i in
                    Item.query.filter_by(type=item_type)]
    @classmethod
    def get_item(cls, itemid):
        item = cls.query.filter_by(id=itemid).first()
        return {
            'id': item.id,
            "requiredInfo": zip(item.requiredInfo.split(","), Question.questions_for_item(item.requiredInfo.split(","))),
            'description': item.description,
            "url": item.url,
            'itemName': item.itemName,
            "type": item.type,
            "price": item.price,
            'sellix_id': SellixIds.get_sellix_id(item.id)
        }


class Question(db.Model):
    __table__ = db.Table('questions', db.metadata, autoload_with=db.engine)
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_question(cls, itemKey):
        question = cls.query.filter_by(itemKey=itemKey).first()
        if question == None:
            return question
        else:
            return question.itemQuestion

    @classmethod
    def questions_for_item(cls, keys: list):
        ret = []
        for i in keys:
            answer = cls.get_question(i)
            if answer == None:
                print(f"Doesnt exist - {i}")
                return
            ret.append(answer)
        return ret

    @classmethod
    def get_all_questions(cls):
        return [{"itemKey":i.itemKey, "itemQuestion":i.itemQuestion} for i in cls.query.all()]

    @classmethod
    def create_question(cls, itemKey, itemQuestion):
        if cls.query.filter_by(itemKey=itemKey).first() == None:
            cls(itemKey=itemKey, itemQuestion=itemQuestion).save_to_db()
        else:
            raise Exception
    @classmethod
    def delete_question(cls, itemKey):
        if cls.query.filter_by(itemKey=itemKey).first() != None:
            db.session.delete(cls.query.filter_by(itemKey=itemKey).first())
            db.commit()
        else:
            raise Exception

class Group(db.Model):
    __table__ = db.Table('fkgroups', db.metadata, autoload_with=db.engine)
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_groups(cls):
        return [name for name, in cls.query.with_entities(cls.groupName).all()]

    @classmethod
    def add_group(cls, group):
        if cls.query.filter_by(groupName=group).first() == None:
            cls(groupName=group).save_to_db()
        else:
            raise Exception

    @classmethod
    def delete_group(cls, group):
        if cls.query.filter_by(groupName=group).first() == None:
            raise Exception
        else:
            db.session.delete(cls.query.filter_by(groupName=group).first())
            db.session.commit()

# -----------------------------------------
# -------------- ADD PROGRAMS -------------
# -----------------------------------------

def get_date():
    current_datetime = datetime.now()

    formatted_date_time = current_datetime.strftime("%d.%m.%Y %H:%M")

    return formatted_date_time

def is_mobile():
    agent = request.headers.get('User-Agent').lower()
    if 'mobile' in agent or 'android' in agent or 'iphone' in agent:
        return True
    else:
        return False

def get_confirmation_message(recipient_email, ordername, orderid):
    with open("confirmation.html") as f:
        message = f.read()
    message = message.replace("{ordername}", ordername.upper()).replace('{orderid}', orderid)
    msg = MIMEMultipart()
    msg['To'] = recipient_email
    msg['From'] = "fkreceipt.info@gmail.com"
    msg['Subject'] = "Thank you for the purchase! - FK-Receipt"
    msg.attach(MIMEText(message, 'html'))
    return msg

def confirmation(recipient_email, ordername, orderid):
    sender_email = "fkreceipt.info@gmail.com"
    sender_password = "xomriepneohxrdyz"
    message = get_confirmation_message(recipient_email, ordername, orderid)

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()
    smtp_server.login(sender_email, sender_password)

    smtp_server.sendmail(sender_email, recipient_email, message.as_string())
    smtp_server.quit()


# -----------------------------------
# ------------- ROUTING -------------
# -----------------------------------

@app.route('/')
def home():
    best_items = Item.get_best_items()
    print(best_items)
    return render_template('home.html', products=Item.get_best_items())

@app.route('/store', methods=['GET', "POST"])
def store():
    if request.method == "GET":
        return render_template("store.html", products=Item.get_items(item_type='all'), groups=Group.get_groups())
    elif request.method == "POST":
        button_pressed = request.form['buttons']
        return render_template("store.html", products=Item.get_items(item_type=button_pressed), groups=Group.get_groups())

@app.route('/affiliate')
def affiliate():
    return render_template('affiliate.html', products=Item.get_best_items())

@app.route('/contact')
def contact():
    return render_template('contact.html', products=Item.get_best_items())

@app.route('/delivery')
def delivery():
    return render_template('delivery.html', products=Item.get_best_items())

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', products=Item.get_best_items())

@app.route('/items/<itemid>')
def item(itemid):
    ItemInfo = Item.get_item(itemid)
    return render_template('product.html', item=ItemInfo, urls=ItemInfo['url'].split(','))

@app.route("/paid")
def check_paid():
    return render_template("mobile/paid.html" if is_mobile() else "paid.html")

@app.route("/checkout/<itemid>")
def iframe(itemid):
    itemInfo = Item.get_item(itemid)
    session['order_info'] = dict(request.args)
    return render_template('survey.html', price=itemInfo['price'], type=itemInfo['type'], itemid=itemid)

@app.route('/checkout/end')
def checkout_end():
    return render_template('survey_end.html')

@app.route("/webhook/<sec>", methods=['POST'])
def make_order(sec):
    try:
        data = json.loads(request.data.decode("utf-8"))
        if sec == secret:
            if data['event'] == "order:paid:product":
                # --------------- EMAIL
                if "email" not in data['data']['custom_fields']:
                    data['data']['custom_fields']['email'] = data['data']['customer_email']
                # --------------- ORDERNAME
                data['data']['custom_fields']['ordername'] = data['data']['product_title']
                # --------------- ADD_SERVICE
                if len(data['data']['discount_breakdown']['addons']) == 1:
                    print("ADDON")
                    data['data']['custom_fields']['add_service'] = True
                else:
                    data['data']['custom_fields']['add_service'] = False
                # --------------- ORDER_DATE
                data['data']['custom_fields']['order_date'] = get_date()

                print(data['data']['custom_fields'])
                if not data['data']['custom_fields']['add_service']:
                    print(data['data']["custom_fields"])
                    status = send_receipt(dict(data['data']["custom_fields"]))
                    print('---------------')
                    print("STATUS")
                    print(status)
                    print('---------------')
                    confirmation(data['data']['custom_fields']['email'], data['data']['custom_fields']['ordername'],
                                 data['data']["uniqid"])
                    Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], status,
                                     datetime.strptime(data['data']['custom_fields']['order_date'], "%d.%m.%Y %H:%M"))
                else:
                    if "EMAIL" in data['data']['custom_fields']['ordername']:
                        print(data['data']["custom_fields"])
                        status = send_receipt(dict(data['data']["custom_fields"]))
                        print('---------------')
                        print("STATUS")
                        print(status)
                        print('---------------')
                        confirmation(data['data']['custom_fields']['email'],
                                     data['data']['custom_fields']['ordername'] + " + " + data['data']['custom_fields'][
                                         'ordername'].replace("EMAIL", "PAPER"),
                                     data['data']["uniqid"])
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], status,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                    elif "PAPER" in data['data']['custom_fields']['ordername']:
                        print(data['data']["custom_fields"])
                        status = send_receipt(dict(data['data']["custom_fields"]))
                        print('---------------')
                        print("STATUS")
                        print(status)
                        print('---------------')
                        print()
                        confirmation(data['data']['custom_fields']['email'],
                                     data['data']['custom_fields']['ordername'] + " + " + data['data']['custom_fields'][
                                         'ordername'].replace("PAPER", "EMAIL"),
                                     data['data']["uniqid"])
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                    else:
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))

                    return jsonify({'status': '200'}), 200
                return jsonify({'status': '200'}), 200
            else:
                return jsonify({'status': '200'}), 200
        else:
            return jsonify({'status': '404'}), 404
    except Exception as e:
        return jsonify({'status': '500', "Exception": e}), 500


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "GET":
        return render_template('admin/mobile/admin.html' if is_mobile() else 'admin/admin.html', wrong = "")
    elif request.method == "POST":
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        if session['username'] == admin_username and session['password'] == admin_passw:
            return redirect(url_for("add_item"))
        else:
            return render_template('admin/mobile/admin.html' if is_mobile() else 'admin/admin.html', wrong = "Wrong password")

@app.route('/add_item', methods=["GET", "POST"])
def add_item():
    if request.method == 'GET':
        if session['username'] == admin_username and session['password'] == admin_passw:
            return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_1='', color="black", questions=Question.get_all_questions(), groups=Group.get_groups())
    elif request.method == "POST":
        if session['username'] == admin_username and session['password'] == admin_passw:
            if 'url' in request.form:
                try:
                    Item.create_item(requiredInfo=request.form['requiredInfo'],
                                      description=request.form['description'],
                                      url=request.form['url'],
                                      thumbnailUrl=request.form['thumbnailUrl'],
                                      itemName=request.form['itemName'],
                                      type = request.form['type'],
                                      price=request.form['price'])
                    database_id = Item.query.filter_by(url=request.form['url']).first().id
                    client = Sellix("6pdLxUB8cSdkFZXtxxXwxFg7mHMDHJ4To6lY3Cmbu53VrkEv74101slMLuRZup3X", 'fkpayment')
                    sellix_id = client.create_product(title=request.form['itemName'], redirect_link="https://fk-receipts.com/delivery",
                                          theme="dark", gateways=["PAYPAL", "USDT", "LITECOIN"], price=request.form['price'],
                                          description=request.form['description'],
                                          webhooks=["https://fk-receipts.com/webhook/AD2583878CFD5"],
                                          dynamic_webhook="https://fk-receipts.com/webhook/AD2583878CFD5",
                                          custom_fields=[{
                                              "type": "text",
                                              "name": "Instagram",
                                              "regex": None,
                                              "placeholder": "instagram",
                                              "default": None,
                                              "required": True
                                          }], type="SERVICE")
                    SellixIds.create_row(database_id=database_id, sellix_id=sellix_id)
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_1='The item was added succesfully', color="green", questions=Question.get_all_questions(), groups=Group.get_groups())
                except Exception:
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_1='The item was NOT added. Smth went wrong', color="red", questions=Question.get_all_questions(), groups=Group.get_groups())
            elif 'question_key' in request.form:
                try:
                    Question.create_question(request.form['question_key'], request.form['question'])
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_2='The question was added successfully!', color="green", questions=Question.get_all_questions(), groups=Group.get_groups())
                except Exception:
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_2='Smth went wrong(Most probably question with this key already exist)', color="red", questions=Question.get_all_questions(), groups=Group.get_groups())
            elif 'question_key_delete' in request.form:
                try:
                    Question.delete_question(request.form['question_key_delete'])
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_3='Successfully  deleted', color="green", questions=Question.get_all_questions(), groups=Group.get_groups())
                except Exception:
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_3='Smth went wrong(Most probably question with this key doesnt exist)', color="red", questions=Question.get_all_questions(), groups=Group.get_groups())
            elif 'add_group' in request.form:
                try:
                    Group.add_group(request.form['add_group'])
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_4='Successfully  added', color="green", questions=Question.get_all_questions(), groups=Group.get_groups())
                except Exception as e:
                    print(e)
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_4='Smth went wrong(Most probably group with this key exist)', color="red", questions=Question.get_all_questions(), groups=Group.get_groups())
            elif 'delete_group' in request.form:
                try:
                    Group.delete_group(request.form['delete_group'])
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_5='Successfully  deleted', color="green", questions=Question.get_all_questions(), groups=Group.get_groups())
                except Exception:
                    return render_template('admin/mobile/add-item.html' if is_mobile() else 'admin/add-item.html', wrong_5='Smth went wrong(Most probably group with this key does not exist)', color="red", questions=Question.get_all_questions(), groups=Group.get_groups())

@app.route("/add_automated_receipt", methods=["GET", "POST"])
def add_automated_receipt():
    if request.method == "GET":
        if session['username'] == admin_username and session['password'] == admin_passw:
            return render_template('admin/mobile/add-automated-receipt.html' if is_mobile() else 'admin/add-automated-receipt.html', wrong="", color_wrong="white", receipts=get_all_automated_receipts(), wrong_delete="")
    else:
        if session['username'] == admin_username and session['password'] == admin_passw:
            if "short_receipt_name" not in request.form:
                if session['username'] == admin_username and session['password'] == admin_passw:
                    try:
                        html_code = request.files['file'].read()
                        date_format = request.form['date_format']
                        if date_format == "-":
                            date_format = ""
                        new_receipt(html_code=html_code.decode("utf-8"),
                                                date_format=date_format,
                                                random_formats=request.form['random_formats'],
                                                subject=request.form['subject'],
                                                receipt_name=request.form['receipt_name'],
                                                email = request.form['email'],
                                                password = request.form['password'])
                        return render_template('admin/mobile/add-automated-receipt.html' if is_mobile() else 'admin/add-automated-receipt.html', wrong="Receipt was saved", color_wrong="green", receipts=get_all_automated_receipts(), wrong_delete="")
                    except Exception as e:
                        return render_template('admin/mobile/add-automated-receipt.html' if is_mobile() else 'admin/add-automated-receipt.html', wrong=str(e), color_wrong="red", receipts=get_all_automated_receipts(), wrong_delete="")
            else:
                try:
                    delete_automated_receipt(request.form['short_receipt_name'])
                    return render_template('admin/mobile/add-automated-receipt.html' if is_mobile() else 'admin/add-automated-receipt.html', wrong="", color_wrong="green", wrong_delete="The Receipt was deleted", receipts=get_all_automated_receipts())
                except Exception as e:
                    return render_template('admin/mobile/add-automated-receipt.html' if is_mobile() else 'admin/add-automated-receipt.html', wrong="", color_wrong="red", wrong_delete=str(e))

@app.route("/generator", methods=["GET"])
def generator():
    if request.method == "GET":
        items = Item.get_items(item_type="all")
        if session['username'] == admin_username and session['password'] == admin_passw:
            return render_template('admin/mobile/generator.html' if is_mobile() else 'admin/generator.html', products=items)

@app.route("/generator/<itemid>", methods=["GET", "POST"])
def single_generator(itemid):
    if request.method == "GET":
        if session['username'] == admin_username and session['password'] == admin_passw:
            ItemInfo = Item.get_item(itemid)
            return render_template('admin/mobile/single_generator.html' if is_mobile() else 'admin/single_generator.html', item=ItemInfo, urls=ItemInfo['url'].split(','), wrong="", color="")
    elif request.method == "POST":
        if session['username'] == admin_username and session['password'] == admin_passw:

            ItemInfo = Item.get_item(itemid)
            order = dict(request.form)
            order['ordername'] = ItemInfo['itemName']
            try:
                status = send_receipt(order)
                if status[0] == False:
                    raise Exception(status[1])
                return render_template('admin/mobile/single_generator.html' if is_mobile() else 'admin/single_generator.html', item=ItemInfo, urls=ItemInfo['url'].split(','), wrong="The receipt was sent", color="green")
            except Exception as e:
                return render_template('admin/mobile/single_generator.html' if is_mobile() else 'admin/single_generator.html', item=ItemInfo, urls=ItemInfo['url'].split(','), wrong=str(e), color="red")





@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'GET':
        if session['username'] == admin_username and session['password'] == admin_passw:
            items = Item.get_items(item_type="all")
            return render_template('admin/mobile/delete-item.html' if is_mobile() else 'admin/delete-item.html', products=items)
    elif request.method == 'POST':
        if session['username'] == admin_username and session['password'] == admin_passw:
            try:
                client = Sellix("6pdLxUB8cSdkFZXtxxXwxFg7mHMDHJ4To6lY3Cmbu53VrkEv74101slMLuRZup3X", 'fkpayment')
                item_id = request.form['delete']
                Item.delete_item(item_id)
                items = Item.get_items(item_type="all")
                sellix_id = SellixIds.get_sellix_id(item_id)
                client.delete_product(sellix_id)
                return render_template('admin/mobile/delete-item.html' if is_mobile() else 'admin/delete-item.html', products=items, color="green", wrong='Product has deleted successfully!')
            except Exception as e:
                print(e)
                items = Item.get_items(item_type="all")
                return render_template('admin/mobile/delete-item.html' if is_mobile() else 'admin/delete-item.html', products=items, color="red", wrong='Smth went wrong, product is not deleted')



@app.route("/orders", methods=['GET', "POST"])
def orders():
    if request.method == "GET":
        if session['username'] == admin_username and session['password'] == admin_passw:
            orders = Order.get_orders()
            return render_template('admin/mobile/orders.html' if is_mobile() else 'admin/orders.html', orders=orders)

    elif request.method == "POST":
        if session['username'] == admin_username and session['password'] == admin_passw:
            if "not-done" in request.form and request.form["search"] == '':
                orders = Order.get_orders(done=False)
            elif "not-done" in request.form and request.form["search"] != '':
                if Order.get_order(request.form['search']) == None:
                    orders = Order.get_orders(email=request.form["search"], done=False)
                else:
                    orders = [Order.get_order(request.form['search'])]
            elif request.form["search"] != '':
                if Order.get_order(request.form['search']) == None:
                    print('ALL/EMAIL')
                    orders = Order.get_orders(email=request.form["search"])
                else:
                    print('ALL/ID_2')
                    orders = [Order.get_order(request.form['search'])]
                    print(orders)
            elif request.form['search'] == "":
                print('ALL/NO EMAIL OR ID')
                orders = Order.get_orders()
            return render_template('admin/mobile/orders.html' if is_mobile() else 'admin/orders.html', orders=orders)

@app.route("/checkcheck")
def checkcheck():
    if session['username'] == admin_username and session['password'] == admin_passw:
        return render_template("CheckCheck/index.html")


@app.route("/orders/<orderid>", methods=['GET', "POST"])
def order(orderid):
    if request.method == "GET":
        if session['username'] == admin_username and session['password'] == admin_passw:
            orderinfo = Order.get_order(orderid)
            return render_template('admin/mobile/order.html' if is_mobile() else 'admin/order.html', orderinfo = orderinfo, add = json.loads(orderinfo['orderContent']), actionStatus='', color='black')
    elif request.method == 'POST':
        if session['username'] == admin_username and session['password'] == admin_passw:
            if request.form['buttons'] == 'mark-as-done':
                try:
                    Order.mark_as_done(orderid)
                    orderinfo = Order.get_order(orderid)
                    return render_template('admin/mobile/order.html' if is_mobile() else 'admin/order.html', orderinfo = orderinfo, add = json.loads(orderinfo['orderContent']), actionStatus="The action was completed!", color='green')
                except Exception:
                    orderinfo = Order.get_order(orderid)
                    return render_template('admin/mobile/order.html' if is_mobile() else 'admin/order.html', orderinfo = orderinfo, add = json.loads(orderinfo['orderContent']), actionStatus="Smth happened. The action was no completed", color='red')

            elif request.form['buttons'] == 'resend':
                try:
                    orderinfo = Order.get_order(orderid)
                    status = send_receipt(json.loads(orderinfo['orderContent']))
                    if status[0] == False:
                        raise Exception(status[1])
                    orderinfo = Order.get_order(orderid)
                    return render_template('admin/mobile/order.html' if is_mobile() else 'admin/order.html', orderinfo = orderinfo, add = json.loads(orderinfo['orderContent']),actionStatus="The action was completed", color='green')
                except Exception as e:
                    orderinfo = Order.get_order(orderid)
                    return render_template('admin/mobile/order.html' if is_mobile() else 'admin/order.html', orderinfo = orderinfo, add = json.loads(orderinfo['orderContent']), actionStatus=str(e), color='red')

# @app.route("/promocodes", methods=['GET', "POST"])
# def promocodes():
#     if request.method == "GET":
#         if session['username'] == admin_username and session['password'] == admin_passw:
#             return render_template("admin/promocodes.html", promocodes=PromoCode.get_promocodes())
#     elif request.method == "POST":
#         if session['username'] == admin_username and session['password'] == admin_passw:
#             if 'delete' in request.form:
#                 PromoCode.delete_promo(request.form['delete'])
#                 return render_template("admin/promocodes.html", promocodes=PromoCode.get_promocodes())
#             else:
#                 PromoCode.save_promocode(request.form['code'], request.form['discount'])
#                 return render_template("admin/promocodes.html", promocodes=PromoCode.get_promocodes())

if __name__=='__main__':
    app.run(host='0.0.0.0')


def simulate_webhook(payload):
    try:
        sec = "AD2583878CFD5"
        data = payload
        if sec == secret:
            if data['event'] == "order:paid:product":
                # --------------- EMAIL
                if "email" not in data['data']['custom_fields']:
                    data['data']['custom_fields']['email'] = data['data']['customer_email']
                # --------------- ORDERNAME
                data['data']['custom_fields']['ordername'] = data['data']['product_title']
                # --------------- ADD_SERVICE
                print(data['data']['discount_breakdown'].keys())
                if len(data['data']['discount_breakdown']['addons']) == 1:
                    print("ADDON")
                    data['data']['custom_fields']['add_service'] = True
                else:
                    data['data']['custom_fields']['add_service'] = False
                # --------------- ORDER_DATE
                data['data']['custom_fields']['order_date'] = get_date()

                print(data['data']['custom_fields'])
                if not data['data']['custom_fields']['add_service']:
                    print(data['data']["custom_fields"])
                    status = send_receipt(data['data']["custom_fields"])
                    print('---------------')
                    print("STATUS")
                    print(status)
                    print('---------------')
                    confirmation(data['data']['custom_fields']['email'], data['data']['custom_fields']['ordername'],
                                 data['data']["uniqid"])
                    Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], status,
                                     datetime.strptime(data['data']['custom_fields']['order_date'], "%d.%m.%Y %H:%M"))
                else:
                    if "EMAIL" in data['data']['custom_fields']['ordername']:
                        print(data['data']["custom_fields"])
                        status = send_receipt(data['data']["custom_fields"])
                        print('---------------')
                        print("STATUS")
                        print(status)
                        print('---------------')
                        confirmation(data['data']['custom_fields']['email'],
                                     data['data']['custom_fields']['ordername'] + " + " + data['data']['custom_fields'][
                                         'ordername'].replace("EMAIL", "PAPER"),
                                     data['data']["uniqid"])
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], status,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                    elif "PAPER" in data['data']['custom_fields']['ordername']:
                        print(data['data']["custom_fields"])
                        status = send_receipt(data['data']["custom_fields"])
                        print('---------------')
                        print("STATUS")
                        print(status)
                        print('---------------')
                        print()
                        confirmation(data['data']['custom_fields']['email'],
                                     data['data']['custom_fields']['ordername'] + " + " + data['data']['custom_fields'][
                                         'ordername'].replace("PAPER", "EMAIL"),
                                     data['data']["uniqid"])
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                    else:
                        Order.save_order(data['data']['uniqid'], data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))
                        Order.save_order(data['data']['uniqid'] + "addServ", data['data']['custom_fields'], False,
                                         datetime.strptime(data['data']['custom_fields']['order_date'],
                                                           "%d.%m.%Y %H:%M"))

                    return jsonify({'status': '200'}), 200
                return jsonify({'status': '200'}), 200
            else:
                print()
                return jsonify({'status': '200'}), 200
        else:
            return jsonify({'status': '404'}), 404
    except Exception as e:
        return jsonify({'status': '500', "Exception": e}), 500

# print(simulate_webhook({"event":"order:paid:product","data":{"id":10181553,"uniqid":"e3f625-2d3d89503a-e299d2","recurring_billing_id":None,"payout_configuration":None,"type":"PRODUCT","subtype":None,"origin":"EMBED","total":9.5,"total_display":9.5,"product_variants":None,"exchange_rate":1,"crypto_exchange_rate":0,"currency":"USD","shop_id":366695,"shop_image_name":"0fecc82a0402f217654a2730f229fb2724b32e1e59a7f682c7ed743fed9661c7.jpg","shop_image_storage":"SHOPS","shop_cloudflare_image_id":"0e43aea2-6fb1-4c74-966a-1e5f76824000","name":"fkpayment","customer_email":"jeppebjodstruplarsen@gmail.com","customer_id":"cst_1d77b482299285d15884f9","affiliate_revenue_customer_id":None,"paypal_email_delivery":True,"product_id":"65cf2c9e8dca3","product_title":"GOAT EMAIL INVOICE","product_type":"SERVICE","subscription_id":None,"subscription_time":None,"gateway":"PAYPAL","blockchain":None,"paypal_apm":None,"stripe_apm":None,"paypal_email":None,"paypal_order_id":"2EM112076C722493C","paypal_payer_email":"jeppebjodstruplarsen@gmail.com","paypal_fee":0.62,"paypal_subscription_id":None,"paypal_subscription_link":None,"lex_order_id":None,"lex_payment_method":None,"paydash_paymentID":None,"virtual_payments_id":None,"stripe_client_secret":None,"stripe_price_id":None,"skrill_email":None,"skrill_sid":None,"skrill_link":None,"perfectmoney_id":None,"binance_invoice_id":None,"binance_qrcode":None,"binance_checkout_url":None,"crypto_address":None,"crypto_amount":0,"crypto_received":0,"crypto_uri":None,"crypto_confirmations_needed":1,"crypto_scheduled_payout":False,"crypto_payout":0,"fee_billed":True,"bill_info":None,"cashapp_qrcode":None,"cashapp_note":None,"cashapp_cashtag":None,"country":"DK","location":"Aarhus, Central Jutland (Europe/Copenhagen)","ip":"84.238.45.160","is_vpn_or_proxy":False,"user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36","quantity":1,"coupon_id":None,"custom_fields":{"us_size":"11","cur":"USD","price":"610","ship":"17.19","total":"651.59","adress":"Beatesmindevej 12 Th2 To The Right","region":"Gug","city":"Aalborg S\u00d8","zip_code":"9210","country":"Danmark","name":"Jeppe Larsen","surname":"Jeppe L","brand":"Air Jordan","name_prod":"Jordan 4 Retro White Oreo","colorway":" WHITE/TECH GREY-BLACK-FIRE RED","img_url":"https://www.goat.com/sneakers/air-jordan-4-retro-oreo-ct8527-100","style":" CT8527-100","email":"jeppebjodstruplarsen@gmail.com","Instagram":"official.jeppe","acf_name":"Jeppe Larsen","acf_surname":"Jeppe L"},"developer_invoice":False,"developer_title":None,"developer_webhook":None,"developer_return_url":None,"status":"COMPLETED","status_details":None,"void_details":None,"discount":0,"fee_percentage":5,"fee_breakdown":"{\"service_fee\": {\"amount\": 0.73, \"currency\": \"USD\", \"breakdown\": {\"flat\": {\"amount\": 0.25, \"currency\": \"USD\"}, \"percentage\": {\"plan\": \"FREE\", \"value\": 5, \"amount\": 0.48, \"currency\": \"USD\"}}}, \"aml_analysis\": {\"amount\": 0, \"currency\": \"USD\", \"breakdown\": {\"wallet\": {\"amount\": 0, \"currency\": \"USD\"}, \"transaction\": {\"amount\": 0, \"currency\": \"USD\"}}}, \"platform_fee\": {\"amount\": 0, \"currency\": \"USD\", \"breakdown\": {\"flat\": {\"amount\": 0, \"currency\": \"USD\"}, \"percentage\": {\"amount\": 0, \"currency\": \"USD\"}}}}","discount_breakdown":{"log":{"coupon":{"total":9.5,"coupon":0,"total_display":9.5,"coupon_display":0},"bundle_discount":[],"volume_discount":{"total":9.5,"total_display":9.5,"volume_discount":0,"volume_discount_display":0}},"tax":{"percentage":0},"addons":[],"coupon":[],"tax_log":{"vat":0,"type":"EXCLUSIVE","vat_total":0,"total_pre_vat":9.5,"total_with_vat":9.5,"vat_percentage":0,"vat_total_display":0,"total_pre_vat_display":9.5,"total_with_vat_display":9.5},"products":[],"currencies":{"default":"USD","display":"USD"},"gateway_fee":[],"price_discount":[],"bundle_discounts":[],"volume_discounts":{"65cf2c9e8dca3":{"type":None,"amount":0,"percentage":None,"amount_display":0}}},"day_value":18,"day":"Sun","month":"Feb","year":2024,"product_addons":None,"bundle_config":None,"created_at":1708285818,"updated_at":1708285863,"updated_by":0,"approved_address":None,"service_text":"","ip_info":{"id":5065307,"request_id":"7HWeZycrvt","ip":"84.238.45.160","user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36","user_language":"en-GB,en-US;q=0.9,en;q=0.8,da;q=0.7","fraud_score":0,"country_code":"DK","region":"Central Jutland","city":"Aarhus","isp":"Bolignet-Aarhus","asn":33796,"organization":"Bolignet-Aarhus","latitude":"56.15000","longitude":"10.22000","is_crawler":0,"timezone":"Europe/Copenhagen","mobile":0,"host":"84-238-45-160.ptr.bnaa.dk","proxy":0,"vpn":0,"tor":0,"active_vpn":0,"active_tor":0,"recent_abuse":0,"bot_status":0,"connection_type":"Residential","abuse_velocity":"none","operating_system":"Windows 10","browser":"Chrome 105.0","device_brand":"N/A","device_model":"N/A","created_at":1663521358,"updated_at":0},"webhooks":[{"uniqid":"65d25f7a09160","url":"https://fk-receipts.com/webhook/AD2583878CFD5","event":"order:created:product","retries":1,"response_code":200,"created_at":1708285818},{"uniqid":"65d25fa7243ef","url":"https://fk-receipts.com/webhook/AD2583878CFD5","event":"order:paid:product","retries":4,"response_code":500,"created_at":1708285863}],"rewards_data":[],"paypal_dispute":None,"product_downloads":[],"payment_link_id":None,"license":False,"status_history":[{"id":29178024,"invoice_id":"e3f625-2d3d89503a-e299d2","status":"CHECKOUT_ORDER_APPROVED","details":"An order has been approved by buyer","created_at":1708285817},{"id":29177997,"invoice_id":"e3f625-2d3d89503a-e299d2","status":"PENDING","details":"The invoice has been created (gateway PAYPAL) and we are now waiting to receive a payment.","created_at":1708285818},{"id":29178041,"invoice_id":"e3f625-2d3d89503a-e299d2","status":"PAYMENT_CAPTURE_COMPLETED","details":"Payment completed for $ 9.5 USD","created_at":1708285849},{"id":29178027,"invoice_id":"e3f625-2d3d89503a-e299d2","status":"COMPLETED","details":"The PayPal invoice has been flagged as completed.","created_at":1708285863}],"aml_wallets":[],"crypto_transactions":[],"paypal_client_id":"AfchO-brJst3wSN2pJl2DouHezOcK49AMaGZiyRsCxyOFiQm1Webm3u3lhiddsCpaEvt49POH2UfsApr","product":{"uniqid":"65cf2c9e8dca3","title":"GOAT EMAIL INVOICE","redirect_link":"https://fk-receipts.com/delivery","description":"New 2024 updated Email Receipt that is fully customized according to your entered data. Email receipt will be generated instantly and send to your e-mail Inbox or Spam folder","price_display":9.5,"currency":"USD","image_name":None,"image_storage":None,"pay_what_you_want":0,"affiliate_revenue_percent":0,"cloudflare_image_id":None,"label_singular":None,"label_plural":None,"feedback":{"total":0,"positive":0,"neutral":0,"negative":0,"list":[]},"average_score":None,"id":0,"shop_id":0,"price":0,"quantity_min":0,"quantity_max":0,"quantity_warning":0,"gateways":[None],"crypto_confirmations_needed":0,"max_risk_level":0,"block_vpn_proxies":False,"private":False,"stock":0,"unlisted":False,"sort_priority":0,"created_at":0,"updated_at":0,"updated_by":0},"total_conversions":{"CAD":12.82,"HKD":74.31,"ISK":1311,"PHP":531.71,"DKK":65.74,"HUF":3426.02,"CZK":224.45,"GBP":7.54,"RON":43.9,"SEK":99.27,"IDR":148728.2,"INR":788.65,"BRL":47.19,"RUB":878.7,"HRK":66.79,"JPY":1428.05,"THB":343.5,"CHF":8.36,"EUR":8.82,"MYR":45.41,"BGN":17.26,"TRY":290.22,"CNY":67.64,"NOK":100.03,"NZD":15.5,"ZAR":179.49,"USD":"9.50","MXN":162.15,"SGD":12.79,"AUD":14.54,"ILS":34.26,"KRW":12659.51,"PLN":38.24,"crypto":{"BTC":"0.0001834682","DOGE":"111.7050028438","BNB":"0.0270020328","ETH":"0.0033547928","LTC":"0.1346441405","BCH":"0.0353338957","NANO":"7.0977516781","XMR":"0.0776026920","SOL":"0.0842166394","XRP":"17.0028259592","CRO":"105.1377614555","USDC":"9.5000000000","USDC_NATIVE":"9.5000000000","USDT":"9.4965864275","TRX":"70.3584673651","CCD":"1517.9905950458","MATIC":"9.7432955460","APE":"5.4982545508","PEPE":"7917300.0506707197","DAI":"9.4988631524","WETH":"0.0033595144","SHIB":"975905.3088324260"}},"theme":"light","dark_mode":0,"crypto_mode":None,"products":[{"uniqid":"65cf2c9e8dca3","title":"GOAT EMAIL INVOICE","redirect_link":"https://fk-receipts.com/delivery","description":"New 2024 updated Email Receipt that is fully customized according to your entered data. Email receipt will be generated instantly and send to your e-mail Inbox or Spam folder","price_display":"9.50","currency":"USD","image_name":None,"image_storage":None,"pay_what_you_want":0,"affiliate_revenue_percent":0,"cloudflare_image_id":None,"label_singular":None,"label_plural":None,"feedback":{"total":0,"positive":0,"neutral":0,"negative":0,"list":[]},"average_score":None}],"gateways_available":["USDT:BEP20","USDT:ERC20","USDT:TRC20","USDT:MATIC","LITECOIN","PAYPAL"],"shop_payment_gateways_fees":[],"shop_paypal_credit_card":True,"shop_force_paypal_email_delivery":True,"shop_walletconnect_id":None,"rates_snapshot":{"id":2425,"USD":"1.0000","CAD":"1.3485","HKD":"7.8220","ISK":"137.9995","PHP":"55.9700","DKK":"6.9205","HUF":"360.6075","CZK":"23.6226","GBP":"0.7935","RON":"4.6210","SEK":"10.4494","IDR":"15655.6000","INR":"83.0163","BRL":"4.9671","RUB":"92.4950","HRK":"7.0301","JPY":"150.3315","THB":"36.1575","CHF":"0.8807","EUR":"0.9278","MYR":"4.7799","BGN":"1.8173","TRY":"30.5488","CNY":"7.1196","NOK":"10.5295","NZD":"1.6331","ZAR":"18.8825","MXN":"17.0824","SGD":"1.3465","AUD":"1.5314","ILS":"3.6059","KRW":"1332.5799","PLN":"4.0254","created_at":1708282803,"updated_at":0,"":0,"BTC":"51800.98509856","DOGE":"0.08517162","BNB":"351.665041716870","ETH":"2834.58281007","LTC":"70.59731159","BCH":"269.10582009","NANO":"1.33792332","XMR":"122.06390277","SOL":"112.83710623","XRP":"0.55922773","CRO":"0.09032635","USDC":"1.00","USDC_NATIVE":"1.00000000","USDT":"1.000289936854","TRX":"0.135061285548","CCD":"0.006209578128","MATIC":"0.97816021","APE":"1.726754647723","PEPE":"0.000001203447","DAI":"1.000156341907","WETH":"2826.405787213200","SHIB":"0.000009745172"},"void_times":[{"gateways":["STRIPE","PAYPAL","SKRILL","PERFECT_MONEY","CASH_APP"],"conf":{"void":86400,"wait_period":None}},{"gateways":["BITCOIN","LITECOIN","DOGECOIN","BITCOIN_CASH","NANO","MONERO","SOLANA","CONCORDIUM","RIPPLE","CRONOS"],"conf":{"void":28800,"wait_period":0,"partial":2592000,"waiting_for_confirmations":2592000}},{"gateways":["BITCOIN_LN"],"conf":{"void":900,"wait_period":None}},{"gateways":["ETHEREUM","USDC:ERC20","USDT:ERC20","PEPE:ERC20","SHIB:ERC20","APE:ERC20","DAI:ERC20"],"conf":{"void":3600,"wait_period":0,"partial":2592000,"waiting_for_confirmations":2592000}},{"gateways":["BINANCE_COIN","TRON","POLYGON","USDC:BEP20","USDC:MATIC","USDC_NATIVE:MATIC","USDT:BEP20","USDT:MATIC","USDT:TRC20","PLZ:BEP20","PLZ:TRC20","DAI:BEP20","DAI:MATIC","WETH:BEP20","WETH:MATIC","SHIB:BEP20","SHIB:MATIC"],"conf":{"void":7200,"wait_period":0,"partial":2592000,"waiting_for_confirmations":2592000}}]}}))