from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateTimeLocalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange,Regexp
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    email = StringField('Email',
        validators=[
            DataRequired(message="Это поле обязательно"),
            Email(message="Введите корректный email адрес")
        ],
        render_kw={"placeholder": "Email"}
    )
    password = PasswordField('Пароль',
        validators=[
            DataRequired(message="Это поле обязательно"),
            Length(min=6, message="Пароль должен быть не менее 6 символов"),
            Regexp(r'^[a-zA-Z0-9]+$',
                message="Пароль должен содержать только английские буквы и цифры")
        ],
        render_kw={"placeholder": "Пароль"}
    )
    submit = SubmitField('Зарегистрироваться')
class CreateRoomForm(FlaskForm):
    roomName = StringField('Название комнаты',
        validators=[
            DataRequired(),
            Regexp(r'^[a-zA-Zа-яА-Я0-9]+$', message="Название комнаты может содержать только буквы и цифры")
        ])
    roomPassword = PasswordField('Пароль комнаты',
        validators=[
            DataRequired(),
            Regexp(r'^[a-zA-Zа-яА-Я0-9]+$', message="Пароль может содержать только буквы и цифры")
        ])
    username = StringField('Имя пользователя в комнате',
        validators=[
            DataRequired(),
            Regexp(r'^[a-zA-Zа-яА-Я0-9]+$', message="Имя пользователя может содержать только буквы и цифры")
        ])
    submit = SubmitField('Создать комнату')

class HeaderForm(FlaskForm):
    email = StringField('Email', render_kw={"readonly": True})
    logout = SubmitField('Выход', render_kw={"formmethod": "GET"})
class RoomPasswordForm(FlaskForm):
    roomPassword = PasswordField('Пароль комнаты', validators=[DataRequired()])
    userName = StringField("Имя пользователя в комнате", validators=[DataRequired()])
    submit = SubmitField('Войти')
class CreateQueueForm(FlaskForm):
    queueName = StringField('Название очереди', validators=[
        DataRequired(),
        Regexp(r'^[a-zA-Zа-яА-Я0-9\s]+$', message="Название очереди может содержать только буквы, цифры и пробелы")
    ])

    maxEntries = IntegerField('Количество мест', validators=[
        DataRequired(), NumberRange(min=1, message="Количество мест должно быть больше 0")
    ])


    entryDeadline = DateTimeLocalField('Время окончания записи', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    queueExpiration = DateTimeLocalField('Время закрытия очереди', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    roomId = StringField("room_id")
    submit = SubmitField('Создать очередь')
class AddEntryForm(FlaskForm):
    entrySubject = TextAreaField('Запись', validators=[DataRequired()])
    queueId = StringField("queue_id")
    submit = SubmitField('Добавить')
