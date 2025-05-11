from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, URL, Optional

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(message='Это поле обязательно')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Это поле обязательно')])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=3, max=20, message='Имя пользователя должно быть от 3 до 20 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=6, message='Пароль должен содержать минимум 6 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message='Это поле обязательно'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться')

class DestinationForm(FlaskForm):
    name = StringField('Название', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    country = StringField('Страна', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(max=100, message='Название страны не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    image_url = StringField('URL изображения', validators=[
        DataRequired(message='Это поле обязательно'),
        URL(message='Введите корректный URL')
    ])
    rating = FloatField('Рейтинг', validators=[
        Optional(),
        NumberRange(min=0, max=5, message='Рейтинг должен быть от 0 до 5')
    ])
    submit = SubmitField('Создать направление')

class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    bio = TextAreaField('О себе')
    location = StringField('Город', validators=[Length(max=100)])
    avatar = FileField('Аватар', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')