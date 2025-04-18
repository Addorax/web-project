from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'travel_explorer_secret_key'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'travel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text, default="")
    location = db.Column(db.String(100), default="")
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Destination {self.name}, {self.country}>'


with app.app_context():
    db.create_all()

    if not Destination.query.first():
        sample_destinations = [
            Destination(
                name='Париж',
                country='Франция',
                description='Город известный за счет эйфелевой башни, Лувра, и др. исторических достопримечательностей.',
                image_url='/static/images/paris.jpg',
                rating=4.7
            ),
            Destination(
                name='Токио',
                country='Япония',
                description='Метрополия включающая в себя разные стили архитектуры и японской культуры',
                image_url='/static/images/tokyo.jpg',
                rating=4.8
            ),
            Destination(
                name='Нью йорк',
                country='США',
                description='Первоклассные рестораны, знаменитые магазины и известный на весь мир парк',
                image_url='/static/images/nyc.jpg',
                rating=4.6
            ),
            Destination(
                name='Рим',
                country='Италия',
                description='Исторический город достопримечательностей, Колизей, Ватикан, и итальянская кухня.',
                image_url='/static/images/rome.jpg',
                rating=4.5
            ),
            Destination(
                name='Бали',
                country='Индонезия',
                description='Тропический остров известный прекрасными пляжами и культурой страны.',
                image_url='/static/images/bali.jpg',
                rating=4.9
            )
        ]
        db.session.add_all(sample_destinations)
        db.session.commit()


@app.route('/')
def home():
    return render_template('random_city.html')


@app.route('/explore')
def explore():
    featured_destinations = Destination.query.order_by(Destination.rating.desc()).limit(3).all()
    return render_template('index.html', destinations=featured_destinations)


@app.route('/random-destination')
def random_destination():
    all_destinations = Destination.query.all()

    if all_destinations:
        random_dest = random.choice(all_destinations)
        return redirect(url_for('destination_detail', id=random_dest.id))
    else:
        flash('Нет доступных направлений', 'warning')
        return redirect(url_for('home'))


@app.route('/destinations')
def destinations():
    all_destinations = Destination.query.all()
    return render_template('destinations.html', destinations=all_destinations)


@app.route('/destination/<int:id>')
def destination_detail(id):
    destination = Destination.query.get_or_404(id)
    return render_template('destination_detail.html', destination=destination)


@app.route('/search')
def search():
    query = request.args.get('query', '')
    results = []
    if query:
        results = Destination.query.filter(
            (Destination.name.contains(query)) |
            (Destination.country.contains(query)) |
            (Destination.description.contains(query))
        ).all()
    return render_template('search_results.html', results=results, query=query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('Имя пользователя или email уже существуют', 'danger')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Пожалуйста, войдите.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите для просмотра профиля', 'warning')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите для редактирования профиля', 'warning')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        user.bio = request.form.get('bio', '')
        user.location = request.form.get('location', '')

        new_email = request.form.get('email')
        if new_email and new_email != user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash('Этот email уже используется', 'danger')
                return render_template('edit_profile.html', user=user)
            user.email = new_email

        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')