from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sellix import Sellix

app = Flask(__name__)

app.secret_key = b'\x1c\xe1\xe7\x16Ja\xce\x889\x05\xcd\xcd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:vlad2306@localhost/fkdatabase'
db = SQLAlchemy(app)

app.app_context().push()

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

    @classmethod
    def get_all_sellix_ids(cls):
        return cls.query.all()

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
            # 'sellix_id': SellixIds.get_sellix_id(item.id)
        }



#
# for i in SellixIds.get_all_sellix_ids():
#     info = Item.get_item(itemid=i.database_id)
#     custom_fields = []
#     custom_fields.append({
#             "type": "text",
#             "name": "Instagram",
#             "regex": None,
#             "placeholder": "instagram",
#             "default": None,
#             "required": True
#         })
#     print(custom_fields)
#     client.update_product(i.sellix_id, title=info['orderName'], redirect_link="https://fk-receipts.com/delivery", theme="dark", gateways=["PAYPAL","USDT","LITECOIN"], price=info['price'], description=info['description'], webhooks=["https://fk-receipts.com/webhook/AD2583878CFD5"], dynamic_webhook="https://fk-receipts.com/webhook/AD2583878CFD5", custom_fields=custom_fields, type="SERVICE")
