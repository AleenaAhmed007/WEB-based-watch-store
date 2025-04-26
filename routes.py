from flask import render_template, redirect, url_for, request, flash, session
from app import app, db
from models import Users, Watches, Cart, Orders, OrderItems
from forms import RegistrationForm, LoginForm, WatchForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@app.route('/')
def index():
    watches = Watches.query.all()
    return render_template('index.html', watches=watches)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(name=form.name.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password!')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/watches')
def watches():
    gender = request.args.get('gender', None)
    if gender:
        watches = Watches.query.filter_by(gender=gender).all()
    else:
        watches = Watches.query.all()
    return render_template('watches.html', watches=watches)

@app.route('/watch/<int:id>')
def watch_detail(id):
    watch = Watches.query.get_or_404(id)
    return render_template('watch_detail.html', watch=watch)

@app.route('/add_to_cart/<int:watch_id>')
def add_to_cart(watch_id):
    if 'user_id' not in session:
        flash('Please login to add items to cart!')
        return redirect(url_for('login'))
    
    # Check if watch exists
    watch = Watches.query.get_or_404(watch_id)
    
    # Check if item is already in cart
    cart_item = Cart.query.filter_by(user_id=session['user_id'], watch_id=watch_id).first()
    
    if not cart_item:
        new_cart_item = Cart(user_id=session['user_id'], watch_id=watch_id)
        db.session.add(new_cart_item)
        db.session.commit()
        flash('Item added to cart!')
    else:
        flash('Item already in cart!')
    
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart!')
        return redirect(url_for('login'))
    
    cart_items = db.session.query(Cart, Watches).join(Watches).filter(Cart.user_id == session['user_id']).all()
    
    total = sum(float(item.Watches.price) for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    if 'user_id' not in session:
        flash('Please login!')
        return redirect(url_for('login'))
    
    cart_item = Cart.query.get_or_404(id)
    
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart!')
    
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout!')
        return redirect(url_for('login'))
    
    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
    
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
    
    # Create new order
    new_order = Orders(user_id=session['user_id'])
    db.session.add(new_order)
    db.session.flush()
    
    # Add items to order
    for item in cart_items:
        order_item = OrderItems(order_id=new_order.id, watch_id=item.watch_id)
        db.session.add(order_item)
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    flash('Order placed successfully!')
    
    return redirect(url_for('orders'))

from sqlalchemy.orm import joinedload


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login to view your orders!')
        return redirect(url_for('login'))
    
    # Use query.options() to specify joinedload
    user_orders = Orders.query.filter_by(user_id=session['user_id']).\
        options(joinedload(Orders.items).joinedload(OrderItems.watch)).all()
    
    return render_template('orders.html', orders=user_orders)


@app.route('/search')

def search():
    query = request.args.get('query', '').strip()
    results = []

    if query:
        results = Watches.query.filter(Watches.name.ilike(f"%{query}%")).all()

    return render_template('search_results.html', query=query, results=results)

# Admin routes
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    watches = Watches.query.all()
    users = Users.query.all()
    orders = Orders.query.all()
    
    return render_template('admin/index.html',
                           watches=watches, users=users, orders=orders)

@app.route('/admin/watches', methods=['GET', 'POST'])
def admin_watches():
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    form = WatchForm()
    if form.validate_on_submit():
        new_watch = Watches(
            name=form.name.data,
            price=form.price.data,
            gender=form.gender.data
        )
        db.session.add(new_watch)
        db.session.commit()
        flash('Watch added successfully!')
        return redirect(url_for('admin_watches'))
    
    watches = Watches.query.all()
    return render_template('admin/watches.html', watches=watches, form=form)

@app.route('/admin/watch/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_watch(id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    watch = Watches.query.get_or_404(id)
    form = WatchForm()
    
    if form.validate_on_submit():
        watch.name = form.name.data
        watch.price = form.price.data
        watch.gender = form.gender.data
        
        db.session.commit()
        flash('Watch updated successfully!')
        return redirect(url_for('admin_watches'))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.name.data = watch.name
        form.price.data = float(watch.price)
        form.gender.data = watch.gender
    
    return render_template('admin/edit_watch.html', form=form, watch=watch)

@app.route('/admin/watch/delete/<int:id>')
def admin_delete_watch(id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    watch = Watches.query.get_or_404(id)
    
    db.session.delete(watch)
    db.session.commit()
    flash('Watch deleted successfully!')
    
    return redirect(url_for('admin_watches'))

@app.route('/admin/orders')
def admin_orders():
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    orders = db.session.query(Orders, Users).join(Users).all()
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:id>')
def admin_order_detail(id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    order = Orders.query.get_or_404(id)
    items = db.session.query(OrderItems, Watches).join(Watches).filter(OrderItems.order_id == order.id).all()
    total = sum(float(item.Watches.price) for item in items)
    
    return render_template('admin/order_detail.html', order=order, items=items, total=total)