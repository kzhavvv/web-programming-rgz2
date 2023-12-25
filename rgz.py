from flask import Blueprint, redirect, url_for, render_template, request, session, current_app, flash, jsonify
from Db import db
from Db.models import users, Products, Orders, OrderItems
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException


rgz = Blueprint('rgz', __name__)



@rgz.route('/')
@rgz.route('/index')
def start():
    return redirect('/rgz/login', code=302)

@rgz.route('/rgz/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'GET':
        return render_template('login.html')

    username_form = request.form.get('username')
    password_form = request.form.get('password')

    my_user = users.query.filter_by(username=username_form).first()

    if my_user is not None:
        if check_password_hash(my_user.password, password_form):
            login_user(my_user, remember = False)
            return redirect('/rgz/products')
        else: 
            errors.append("Неправильный пароль")
            return render_template('login.html', errors=errors)
        
    if not (username_form or password_form):
        errors.append("Пожалуйста заполните все поля")
        return render_template("login.html", errors=errors)
    if username_form == '':
        errors.append("Пожалуйста заполните все поля")
        print(errors)
        return render_template('login.html', errors=errors)
    if password_form == '':
        errors.append("Пожалуйста заполните все поля")
        print(errors)
        return render_template('login.html', errors=errors)
    else: 
        errors.append('Пользователя не существует')
        return render_template('login.html', errors=errors)
    

@rgz.route('/rgz/register', methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        existing_user = users.query.filter_by(username=username).first()
        if existing_user:
            errors.append("Пользователь уже существует")
            return render_template('register.html', errors=errors)


        hashed_password = generate_password_hash(password)
        new_user = users(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect('/rgz/login')
    return render_template('register.html')
        
@rgz.route('/rgz/products', methods=['GET'])
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Products.query.paginate(page=page, per_page=50)
    return render_template('products.html', products=products)

@rgz.route('/rgz/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    successes = []
    if request.method == 'POST':
        sku = request.form.get('sku')
        name = request.form.get('name')
        quantity = request.form.get('quantity', type=int)

        product = Products.query.filter_by(sku=sku).first()
        if product:
            product.quantity += quantity
        else:
            product = Products(sku=sku, name=name, quantity=quantity)
            db.session.add(product)
        db.session.commit()
        successes.append('Товар добавлен')
        return render_template('add_product.html', successes=successes)
    return render_template('add_product.html')

@rgz.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Products.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products'))

@rgz.route('/rgz/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = request.form.get('quantity', type=int)
    product = Products.query.get_or_404(product_id)

    if product.quantity < quantity:
        flash('Недостаточно в наличии ' + product.name)
        return redirect(url_for('rgz.products'))

    cart_item = {'product_id': product_id, 'quantity': quantity}
    if 'cart' not in session:
        session['cart'] = [cart_item]
    else:
        session['cart'].append(cart_item)

    flash('Товары добавлены в корзину')
    return redirect(url_for('rgz.products'))


@rgz.route('/rgz/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':
        order = Orders()
        for item in session['cart']:
            product = Products.query.get(item['product_id'])
            if product.quantity < item['quantity']:
                flash('Not enough stock for ' + product.name)
                return redirect(url_for('rgz.create_order'))
            order_item = OrderItems(product_id=item['product_id'], quantity=item['quantity'])
            order.items.append(order_item)
            product.quantity -= item['quantity']
        db.session.add(order)
        db.session.commit()
        session['cart'] = []
        return redirect('/rgz/orders')
    else:
        cart_items = []
        for item in session['cart']:
            product = Products.query.get(item['product_id'])
            cart_items.append({'product': product, 'quantity': item['quantity']})
        return render_template('create_order.html', cart=cart_items)

@rgz.route('/rgz/orders', methods=['GET'])
@login_required
def zakaz():
    zakazes = Orders.query.all()
    return render_template('order.html', zakazes=zakazes)

@rgz.route('/rgz/pay_order/<int:order_id>', methods=['POST'])
@login_required
def pay_order(order_id):
    order = Orders.query.get_or_404(order_id)
    order.status = 'paid'
    db.session.commit()
    return redirect('/rgz/orders')

@rgz.route('/rgz/logout')
def logout():
    session.clear()
    return redirect('/rgz/login')

@rgz.errorhandler(KeyError)
def handle_key_error(e):
    flash('Сначала добавьте товар в корзину!')
    return redirect('/rgz/products')