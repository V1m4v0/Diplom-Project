from flask import render_template, request, redirect, url_for, flash, session, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Product, Cart
import os

@app.route('/register', methods=['GET', 'POST'])
def register():
    messages = get_flashed_messages()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают.')
            return redirect(url_for('register'))

        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()

        flash('Пользователь успешно зарегистрирован!')
        return redirect(url_for('store'))

    return render_template('register.html', messages=messages)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    messages = get_flashed_messages()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash('Вы успешно вошли в систему.')
            return redirect(url_for('store'))
        else:
            flash('Неправильное имя пользователя или пароль.')
            return redirect(url_for('login'))

    return render_template('login.html', messages=messages)

@app.route('/store')
def store():
    products = Product.query.all()
    return render_template('store.html', products=products)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session or session['username'] != 'admin':
        flash('Доступ запрещен.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f'/static/uploads/{filename}'
            else:
                flash('Неправильный формат файла.')
                return redirect(url_for('admin'))
        else:
            image_url = None

        new_product = Product(name=name, description=description, price=price, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()

        flash('Товар успешно добавлен!')
        return redirect(url_for('admin'))

    products = Product.query.all()
    return render_template('admin.html', products=products)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'username' not in session:
        flash('Сначала войдите в систему.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    cart_item = Cart(user_id=user.id, product_id=product_id)
    db.session.add(cart_item)
    db.session.commit()

    flash('Товар добавлен в корзину.')
    return redirect(url_for('store'))


@app.route('/cart')
def cart():
    if 'username' not in session:
        flash('Сначала войдите в систему.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    cart_items = Cart.query.filter_by(user_id=user.id).all()
    products = [Product.query.get(item.product_id) for item in cart_items]

    return render_template('cart.html', products=products)


@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        admin_username = request.form['username']
        admin_password = request.form['password']

        existing_admin = User.query.filter_by(username=admin_username).first()
        if existing_admin:
            flash('Администратор уже существует.')
            return redirect(url_for('create_admin'))

        new_admin = User(username=admin_username,
                         password=generate_password_hash(admin_password, method='pbkdf2:sha256'))
        db.session.add(new_admin)
        db.session.commit()

        flash('Администратор успешно создан!')
        return redirect(url_for('login'))

    return render_template('create_admin.html')

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'username' not in session or session['username'] != 'admin':
        flash('Доступ запрещен.')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash('Товар успешно удален!')
    return redirect(url_for('admin'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'username' not in session:
        flash('Сначала войдите в систему.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    cart_item = Cart.query.filter_by(user_id=user.id, product_id=product_id).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Товар удален из корзины.')
    else:
        flash('Товар не найден в корзине.')

    return redirect(url_for('cart'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

