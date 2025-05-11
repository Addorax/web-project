from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import random
import uuid
from forms import LoginForm, RegistrationForm, DestinationForm, EditProfileForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'travel_explorer_secret_key'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'travel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text, default="")
    location = db.Column(db.String(100), default="")
    avatar = db.Column(db.String(200), default="default.jpg")
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


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return new_filename


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
    if 'user_id' in session:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                flash('Это имя пользователя уже занято', 'danger')
            else:
                flash('Этот email уже используется', 'danger')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация успешна! Пожалуйста, войдите.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)


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


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите для редактирования профиля', 'warning')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])
    form = EditProfileForm(obj=user)

    if form.validate_on_submit():
        if form.email.data != user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Этот email уже используется', 'danger')
                return render_template('edit_profile.html', form=form, user=user)

        form.populate_obj(user)

        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename:
                if allowed_file(avatar_file.filename):
                    filename = generate_unique_filename(avatar_file.filename)
                    avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    user.avatar = filename
                else:
                    flash('Недопустимый формат файла. Разрешены только изображения (png, jpg, jpeg, gif)', 'danger')

        db.session.commit()

        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', form=form, user=user)


@app.route('/create-destination', methods=['GET', 'POST'])
def create_destination():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите для создания направления', 'warning')
        return redirect(url_for('login'))

    form = DestinationForm()

    if form.validate_on_submit():
        new_destination = Destination(
            name=form.name.data,
            country=form.country.data,
            description=form.description.data,
            image_url=form.image_url.data,
            rating=form.rating.data or 0.0
        )

        db.session.add(new_destination)
        db.session.commit()

        flash('Направление успешно создано!', 'success')
        return redirect(url_for('destination_detail', id=new_destination.id))

    return render_template('create_destination.html', form=form)


if __name__ == '__main__':
    app.run(debug=True, port=8080)