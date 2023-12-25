from . import db
from flask_login import UserMixin

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), nullable = False, unique = True)
    password = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f'id:{self.id}, username:{self.username}, password:{self.password}'


class Products(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    sku = db.Column(db.String(30), nullable = False, unique = True)
    name = db.Column(db.String(255), nullable = False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'id:{self.id}, sku:{self.sku}, name:{self.name}, quantity:{self.quantity}'
        
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False, default='unpaid')
    items = db.relationship('OrderItems', backref='order', lazy=True)

class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)



