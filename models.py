from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.Enum('user', 'admin'), default='user')
    
    # Relationships
    orders = db.relationship('Orders', backref='user', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Watches(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2))
    gender = db.Column(db.Enum('men', 'women'))
    
    # Relationships
    cart_items = db.relationship('Cart', backref='watch', lazy=True)
    order_items = db.relationship('OrderItems', backref='watch', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    watch_id = db.Column(db.Integer, db.ForeignKey('watches.id'))

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    # Relationships
    items = db.relationship('OrderItems', backref='order', lazy=True)

class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    watch_id = db.Column(db.Integer, db.ForeignKey('watches.id'))
    quantity = db.Column(db.Integer, default=1)

    

    @property
    def subtotal(self):
        return float(self.watch.price) * self.quantity