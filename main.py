import flask_login
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session, products_api
from forms.user import RegisterForm, LoginForm
from data.users import User
from forms.product import ProductsForm
from data.products import Products
from cloudipsp import Api, Checkout
from selenium import webdriver
from forms.select import SelectForm
import oxr
from flask import make_response


#if current_user.is_authenticated - проверка, авторизован ли пользователь




app = Flask(__name__)


app.config['SECRET_KEY'] = '165225asfagblp796796078asdafsaf412fa'


login_manager = LoginManager()
login_manager.init_app(app)


EXCHANGE_RATES = oxr.latest()
countries = EXCHANGE_RATES.keys()





@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/', methods=['GET', 'POST'])
def start():
    form = SelectForm()
    current_rate = 1
    if form.validate_on_submit():
        current_country = form.cur.data
        current_rate = EXCHANGE_RATES[current_country]
    db_sess = db_session.create_session()
    items = db_sess.query(Products).all()
    return render_template("start.html", title='Каталог', data=items,
                           rate=current_rate, form=form)


@app.route('/about')
def about():
    return render_template("About.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            if form.user_type.data == 'Обычный пользователь' and user.type == 'Обычный пользователь':
                return redirect("/start_logged")
            elif form.user_type.data == 'Администратор' and User.type == 'Администратор':
                return redirect("/start_dev_logged")
        return render_template('Login.html',
                                message="Неправильный логин или пароль",
                                form=form)
    return render_template('Login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('Register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('Register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            phone_number=form.phone_number.data,
            email=form.email.data,
            type='Обычный пользователь'
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('Register.html', title='Регистрация', form=form)


@app.route('/start_logged', methods=['GET', 'POST'])
@login_required
def start_logged():
    form = SelectForm()
    current_country_usual = 'USD'
    current_rate_usual = 1
    if form.validate_on_submit():
        current_country_usual = form.cur.data
        current_rate_usual = EXCHANGE_RATES[current_country_usual]
    db_sess = db_session.create_session()
    items = db_sess.query(Products).all()
    return render_template("start_logged.html", title='Каталог', data=items, cur_country=current_country_usual,
                           rate=current_rate_usual, form=form)


@app.route('/about_logged')
@login_required
def about_logged():
    return render_template("About_logged.html", title='О нас')


@app.route('/start_dev_logged', methods=['GET', 'POST'])
@login_required
def start_dev_logged():
    form = SelectForm()
    current_country_dev = 'USD'
    current_rate_dev = 1
    print(1)
    if form.validate_on_submit():
        current_country_dev = form.cur.data
        current_rate_dev = EXCHANGE_RATES[current_country_dev]
        print(current_country_dev, current_rate_dev)
    db_sess = db_session.create_session()
    items = db_sess.query(Products).all()
    return render_template("start_dev_logged.html", title='Каталог', data=items, cur_country=current_country_dev,
                           rate=current_rate_dev, form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/adding', methods=['GET', 'POST'])
@login_required
def adding():
    form = ProductsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Products(name=form.name.data,
                           price=form.price.data,
                           image=form.image.data)
        db_sess.add(product)
        db_sess.commit()
        return redirect('/start_dev_logged')
    return render_template("Adding.html", title='Добавление товара', form=form)


@app.route('/buy/<int:id>:<string:cur_country>:<float:price>')
@login_required
def item_buy(id, cur_country, price):
    db_sess = db_session.create_session()
    item = db_sess.query(Products).filter(Products.id == id).first()
    price = round(price)
    api = Api(merchant_id=1396424,
            secret_key='test')
    checkout = Checkout(api=api)
    data = {
        "currency": cur_country,
        "amount": str(price) + "00"
    }
    db_sess.delete(item)
    db_sess.commit()
    url = checkout.url(data).get('checkout_url')
    return redirect(url)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/orders')
@login_required
def orders():
    return render_template("Orders.html", title='Список заказов')


if __name__ == '__main__':
    db_session.global_init("db/Users.db")
    app.register_blueprint(products_api.blueprint)
    app.run(debug=True)