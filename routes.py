from flask import render_template, redirect, url_for, request, flash, session
from app import app, db
from models import Users, Watches, Cart, Orders, OrderItems
from forms import RegistrationForm, LoginForm, WatchForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import joinedload

# ABSTRACTION
class RouteHandler:
    """Base class - Abstract class that defines common functionality"""
    
    @classmethod
    def handle(cls, *args, **kwargs):
        """Handle the route with proper authentication and error handling"""
        # ABSTRACTION
        try:
            return cls._process(*args, **kwargs)
        except Exception as e:
            flash(f"An error occurred: {str(e)}")
            return redirect(url_for('index'))
    
    @classmethod
    def _process(cls, *args, **kwargs):
        """Main processing logic to be overridden by subclasses"""
        # ABSTRACTION
        pass
    
    @staticmethod
    def check_auth():
        """Check if user is authenticated"""
        # ENCAPSULATION: Encapsulates authentication logic
        if 'user_id' not in session:
            return False
        return True
    
    @staticmethod
    def check_admin():
        """Check if user is admin"""
       
        if 'user_id' not in session or session['user_role'] != 'admin':
            return False
        return True


# INHERITANCE
class IndexRoutes(RouteHandler):
    @classmethod
    def _process(cls):
        # POLYMORPHISM
        watches = Watches.query.all()
        return render_template('index.html', watches=watches)


# INHERITANCE
class AboutRoutes(RouteHandler):
    @classmethod
    def _process(cls):
        # POLYMORPHISM
        return render_template('about.html')


# INHERITANCE
class AuthRoutes(RouteHandler):
    
    @classmethod
    def register(cls):
        if cls.check_auth():
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
    
    @classmethod
    def login(cls):
        if cls.check_auth():
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
    
    @classmethod
    def logout(cls):
        session.pop('user_id', None)
        session.pop('user_role', None)
        flash('You have been logged out.')
        return redirect(url_for('index'))


# INHERITANCE
class WatchRoutes(RouteHandler):
    
    @classmethod
    def list_watches(cls):
        gender = request.args.get('gender', None)
        if gender:
            watches = Watches.query.filter_by(gender=gender).all()
        else:
            watches = Watches.query.all()
        return render_template('watches.html', watches=watches)
    
    @classmethod
    def watch_detail(cls, id):
        watch = Watches.query.get_or_404(id)
        return render_template('watch_detail.html', watch=watch)
    
    @classmethod
    def search(cls):
        query = request.args.get('query', '').strip()
        results = []

        if query:
            results = Watches.query.filter(Watches.name.ilike(f"%{query}%")).all()

        return render_template('search_results.html', query=query, results=results)


# INHERITANCE
class CartRoutes(RouteHandler):
   
    @classmethod
    def _process(cls, *args, **kwargs):
        # POLYMORPHISM:
        if not cls.check_auth():
            flash('Please login to view your cart!')
            return redirect(url_for('login'))
        return cls._handle_cart(*args, **kwargs)
    
    @classmethod
    def _handle_cart(cls, *args, **kwargs):
        """To be implemented by subclasses"""
        # ABSTRACTION
        pass
    
    
    @classmethod
    def view_cart(cls):
        if not cls.check_auth():
            flash('Please login to view your cart!')
            return redirect(url_for('login'))
        
        cart_items = db.session.query(Cart, Watches).join(Watches).filter(Cart.user_id == session['user_id']).all()
        total = sum(float(item.Watches.price) * item.Cart.quantity for item in cart_items)
        
        return render_template('cart.html', cart_items=cart_items, total=total)
    
    @classmethod
    def add_to_cart(cls, watch_id):
        if not cls.check_auth():
            flash('Please login to add items to cart!')
            return redirect(url_for('login'))
        
        # Check if watch exists
        watch = Watches.query.get_or_404(watch_id)
        
        # Check if item is already in cart
        cart_item = Cart.query.filter_by(user_id=session['user_id'], watch_id=watch_id).first()
        
        if not cart_item:
            # Create new cart item with quantity 1
            new_cart_item = Cart(user_id=session['user_id'], watch_id=watch_id, quantity=1)
            db.session.add(new_cart_item)
            flash('Item added to cart!')
        else:
            # Increment quantity of existing cart item
            cart_item.quantity += 1
            flash('Item quantity updated in cart!')
        
        db.session.commit()
        return redirect(url_for('cart'))
    
    @classmethod
    def increase_quantity(cls, cart_id):
        if not cls.check_auth():
            flash('Please login to update your cart!')
            return redirect(url_for('login'))
        
        cart_item = Cart.query.get_or_404(cart_id)
        
        # Make sure the cart item belongs to the logged-in user
        if cart_item.user_id != session['user_id']:
            flash('Unauthorized access!')
            return redirect(url_for('cart'))
        
        cart_item.quantity += 1
        db.session.commit()
        flash('Quantity updated!')
        return redirect(url_for('cart'))
    
    @classmethod
    def decrease_quantity(cls, cart_id):
        if not cls.check_auth():
            flash('Please login to update your cart!')
            return redirect(url_for('login'))
        
        cart_item = Cart.query.get_or_404(cart_id)
        
        # Make sure the cart item belongs to the logged-in user
        if cart_item.user_id != session['user_id']:
            flash('Unauthorized access!')
            return redirect(url_for('cart'))
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
            flash('Quantity updated!')
        else:
            # If quantity would become 0, remove the item from cart
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart!')
        
        return redirect(url_for('cart'))
    
    @classmethod
    def remove_from_cart(cls, id):
        if not cls.check_auth():
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


# INHERITANCE
class OrderRoutes(RouteHandler):
    
    @classmethod
    def checkout(cls):
        if not cls.check_auth():
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
            order_item = OrderItems(order_id=new_order.id, watch_id=item.watch_id, quantity=item.quantity)
            db.session.add(order_item)
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        db.session.commit()
        flash('Order placed successfully!')
        
        return redirect(url_for('orders'))
    
    @classmethod
    def view_orders(cls):
        if not cls.check_auth():
            flash('Please login to view your orders!')
            return redirect(url_for('login'))
        
        # Use query.options() to specify joinedload
        user_orders = Orders.query.filter_by(user_id=session['user_id']).\
            options(joinedload(Orders.items).joinedload(OrderItems.watch)).all()
        
        return render_template('orders.html', orders=user_orders)


# INHERITANCE
class AdminRoutes(RouteHandler):
   
    @classmethod
    def _process(cls, *args, **kwargs):
        # POLYMORPHISM: 
        if not cls.check_admin():
            flash('Unauthorized access!')
            return redirect(url_for('index'))
        return cls._handle_admin(*args, **kwargs)
    
    @classmethod
    def _handle_admin(cls, *args, **kwargs):
        """To be implemented by subclasses"""
       
        pass


# INHERITANCE: 
# This is multi-level inheritance
class AdminDashboardRoutes(AdminRoutes):
    # POLYMORPHISM
    @classmethod
    def index(cls):
        if not cls.check_admin():
            flash('Unauthorized access!')
            return redirect(url_for('index'))
            
        watches = Watches.query.all()
        users = Users.query.all()
        orders = Orders.query.all()
        
        return render_template('admin/index.html',
                            watches=watches, users=users, orders=orders)


# INHERITANCE: 
class AdminWatchRoutes(AdminRoutes):

    @classmethod
    def list_watches(cls):
        if not cls.check_admin():
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
    
    @classmethod
    def edit_watch(cls, id):
        if not cls.check_admin():
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
    
    @classmethod
    def delete_watch(cls, id):
        if not cls.check_admin():
            flash('Unauthorized access!')
            return redirect(url_for('index'))
        
        watch = Watches.query.get_or_404(id)
        
        db.session.delete(watch)
        db.session.commit()
        flash('Watch deleted successfully!')
        
        return redirect(url_for('admin_watches'))


# INHERITANCE
class AdminOrderRoutes(AdminRoutes):
    
    @classmethod
    def list_orders(cls):
        if not cls.check_admin():
            flash('Unauthorized access!')
            return redirect(url_for('index'))
        
        orders = db.session.query(Orders, Users).join(Users).all()
        
        return render_template('admin/orders.html', orders=orders)
    
    @classmethod
    def order_detail(cls, id):
        if not cls.check_admin():
            flash('Unauthorized access!')
            return redirect(url_for('index'))
        
        order = Orders.query.get_or_404(id)
        items = db.session.query(OrderItems, Watches).join(Watches).filter(OrderItems.order_id == order.id).all()
        
        # Update the total calculation to account for quantities
        total = sum(float(item[1].price) * item[0].quantity for item in items)
        
        return render_template('admin/order_detail.html', order=order, items=items, total=total)


# Route registrations using the class methods

@app.route('/')
def index():
    return IndexRoutes.handle()  # POLYMORPHISM
@app.route('/about')
def about():
    return AboutRoutes.handle()  # POLYMORPHISM

@app.route('/register', methods=['GET', 'POST'])
def register():
    return AuthRoutes.register()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return AuthRoutes.login()

@app.route('/logout')
def logout():
    return AuthRoutes.logout()

@app.route('/watches')
def watches():
    return WatchRoutes.list_watches()

@app.route('/watch/<int:id>')
def watch_detail(id):
    return WatchRoutes.watch_detail(id)

@app.route('/add_to_cart/<int:watch_id>')
def add_to_cart(watch_id):
    return CartRoutes.add_to_cart(watch_id)

@app.route('/increase_quantity/<int:cart_id>')
def increase_quantity(cart_id):
    return CartRoutes.increase_quantity(cart_id)

@app.route('/decrease_quantity/<int:cart_id>')
def decrease_quantity(cart_id):
    return CartRoutes.decrease_quantity(cart_id)

@app.route('/cart')
def cart():
    return CartRoutes.view_cart()

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    return CartRoutes.remove_from_cart(id)

@app.route('/checkout')
def checkout():
    return OrderRoutes.checkout()

@app.route('/orders')
def orders():
    return OrderRoutes.view_orders()

@app.route('/search')
def search():
    return WatchRoutes.search()

@app.route('/admin')
def admin():
    return AdminDashboardRoutes.index()

@app.route('/admin/watches', methods=['GET', 'POST'])
def admin_watches():
    return AdminWatchRoutes.list_watches()

@app.route('/admin/watch/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_watch(id):
    return AdminWatchRoutes.edit_watch(id)

@app.route('/admin/watch/delete/<int:id>')
def admin_delete_watch(id):
    return AdminWatchRoutes.delete_watch(id)

@app.route('/admin/orders')
def admin_orders():
    return AdminOrderRoutes.list_orders()

@app.route('/admin/order/<int:id>')
def admin_order_detail(id):
    return AdminOrderRoutes.order_detail(id)