
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
import uuid
import psycopg2
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User
from app import app
import re
import json
from datetime import datetime
from app.forms import LoginForm, RegistrationForm, CreateRoomForm, HeaderForm, RoomPasswordForm, CreateQueueForm, AddEntryForm
routes = Blueprint('routes', __name__)


def connect_to_db():
    conn = None
    try:
        conn = psycopg2.connect(
            host=app.config['DB_HOST'],
            database=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD']
        )
        return conn
    except psycopg2.Error as e:
        app.logger.exception(f"Database connection error: {e}")
        return None
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/', methods=['GET'])
@login_required
def base():
    header_form = HeaderForm()  # Инициализация формы для шапки
    header_form.email.data = current_user.email  # Передача email пользователя в форму
    create_room_form = CreateRoomForm() #инициализация формы создания комнаты
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT r.room_id, r.room_name, rp.role_name
                FROM Rooms r
                INNER JOIN RoomParticipants rp ON r.room_id = rp.room_id
                WHERE rp.email = %s;
            """, (current_user.email,))
            user_rooms = [{'id': row[0], 'name': row[1], 'role': row[2]} for row in cur.fetchall()]

        except psycopg2.Error as e:
            flash(f"Ошибка получения списка комнат: {e}", "error")
            app.logger.exception(f"Database error getting rooms: {e}")
            user_rooms = []
        finally:
            cur.close()
            conn.close()
    else:
        flash("Ошибка подключения к базе данных.", "error")
        user_rooms = []
    return render_template('base.html', rooms=user_rooms, header_form=header_form, create_room_form=create_room_form)
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.base'))
    form = LoginForm()  # Инициализация формы для входа
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT email, password FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user:
                    password_from_db = bytes(user[1])
                    if bcrypt.checkpw(password.encode('utf-8'), password_from_db):
                        user_object = User(email)
                        login_user(user_object)
                        flash(f"Добро пожаловать, {email}!", "success")
                        return redirect(url_for('routes.base'))
                    else:
                        flash("Неверный пароль или почта пользователя!", "error")
                        return render_template("main.html", form=form)
                else:
                    flash("Неверный пароль или почта пользователя!", "error")
                    return render_template("main.html", form=form)
            except psycopg2.Error as e:
                error = f"Ошибка базы данных: {e}"
                flash(error, "error")
                app.logger.exception(f"Database error during login: {e}")
                return render_template("main.html", form=form, error=error)
            except Exception as e:
                error = f"Неизвестная ошибка: {e}"
                flash(error, "error")
                app.logger.exception(f"An unexpected error occurred during login: {e}")
                return render_template("main.html", form=form, error=error)
            finally:
                cur.close()
                conn.close()
        else:
            error = "Ошибка подключения к базе данных. Попробуйте позже."
            flash(error, "error")
            return render_template("main.html", form=form, error=error)
    return render_template("main.html", form=form)
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)


@routes.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Проверка формата email
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            flash("Введите корректный email адрес", "error")
            return render_template("registration.html", form=form)

        # Проверка пароля
        if not re.match(r"^[a-zA-Z0-9]+$", password):
            flash("Пароль должен содержать только английские буквы и цифры", "error")
            return render_template("registration.html", form=form)

        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn = connect_to_db()
            if conn:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
                    conn.commit()
                    flash("Регистрация прошла успешно!", "success")
                    return redirect(url_for('routes.login'))
                except psycopg2.Error as e:
                    if "duplicate key" in str(e).lower():
                        flash("Пользователь с таким email уже существует", "error")
                    else:
                        flash("Ошибка при регистрации", "error")
                finally:
                    cur.close()
                    conn.close()
        except Exception as e:
            flash("Произошла ошибка при регистрации", "error")

    return render_template("registration.html", form=form)


@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/create_queue', methods=['POST'])
def create_queue():
    form = CreateQueueForm(request.form)  # Инициализация формы для создания очереди
    if form.validate():
        try:
            # Достаем данные из формы
            room_id = form.roomId.data
            queue_name = form.queueName.data
            max_entries = form.maxEntries.data
            entry_deadline = form.entryDeadline.data
            queue_expiration = form.queueExpiration.data

            # Проверки:
            # 1. Проверка названия очереди (допустимы только русские, английские буквы, цифры и пробелы)
            if not re.match(r'^[a-zA-Zа-яА-Я0-9\s]+$', queue_name):
                return jsonify({'success': False, 'error': 'Название очереди может содержать только буквы, цифры и пробелы'})

            # 2. Проверка количества мест (должно быть больше 0)
            if max_entries <= 0:
                return jsonify({'success': False, 'error': 'Количество мест должно быть больше 0'})

            # 3. Проверка времени (должно быть не позднее текущей даты)
            current_time = datetime.now()
            if entry_deadline is None or queue_expiration is None:
                return jsonify({'success': False, 'error': 'Не указано время окончания записи или закрытия очереди'})
            if entry_deadline < current_time or queue_expiration < current_time:
                return jsonify({'success': False,'error': 'Время окончания записи или закрытия очереди должно быть позже текущего времени'})

            # Подключение к базе данных
            conn = connect_to_db()
            if not conn:
                return jsonify({'success': False, 'error': 'Ошибка подключения к базе данных'})

            cur = conn.cursor()

            # Добавление очереди в базу данных
            cur.execute("""
                INSERT INTO queues (room_id, queue_name, creation_date, available_entries, entry_end_time, deletion_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING queue_id;
            """, (room_id, queue_name, datetime.now(), max_entries, entry_deadline, queue_expiration))

            # Сохранение изменений в базе
            conn.commit()

            # Получение ID созданной очереди
            queue_id = cur.fetchone()[0]
            cur.close()
            conn.close()

            # Успешное создание очереди
            return jsonify({'success': True, 'queueId': queue_id})

        except psycopg2.Error as e:
            # Обработка ошибок базы данных
            app.logger.exception(f"Database error during queue creation: {e}")
            return jsonify({'success': False, 'error': f'Ошибка базы данных: {e}'})

        except Exception as e:
            # Обработка других ошибок
            app.logger.exception(f"Unexpected error during queue creation: {e}")
            return jsonify({'success': False, 'error': f'Произошла неожиданная ошибка: {e}'})

    # Если форма не прошла валидацию
    return jsonify({'success': False, 'error': form.errors})

@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/create_room', methods=['POST'])
def create_room():
    form = CreateRoomForm(request.form)  # Инициализация формы для создания комнаты
    if form.validate():
        try:
            room_name = form.roomName.data
            room_password = form.roomPassword.data
            username_in_room = form.username.data
            room_id = str(uuid.uuid4())
            conn = connect_to_db()
            if conn:
                cur = conn.cursor()
                try:
                    conn.autocommit = False
                    cur.execute("""
                         INSERT INTO Rooms (room_id, creator_email, room_name, room_password)
                         VALUES (%s, %s, %s, %s);
                     """, (
                        room_id, current_user.email, room_name,
                        bcrypt.hashpw(room_password.encode('utf-8'), bcrypt.gensalt())))
                    cur.execute("""
                         INSERT INTO RoomParticipants (email, room_id, role_name, username_in_room)
                         VALUES (%s, %s, %s, %s);
                     """, (current_user.email, room_id, 'Admin', username_in_room))
                    conn.commit()
                    conn.commit()
                    return jsonify({'success': True, 'roomId': room_id})
                except psycopg2.Error as e:
                    conn.rollback()
                    return jsonify({'success': False, 'error': f"Ошибка базы данных: {e}"})
                except Exception as e:
                    conn.rollback()
                    return jsonify({'success': False, 'error': f"Неизвестная ошибка: {e}"})
                finally:
                    cur.close()
                    conn.close()
            else:
                return jsonify({'success': False, 'error': "Ошибка подключения к базе данных."})
        except Exception as e:
            return jsonify({'success': False, 'error': f"Ошибка обработки запроса: {e}"})
    return jsonify({'success': False, 'error': form.errors})
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/my_rooms')
@login_required
def my_rooms():
    return redirect(url_for('routes.base'))


@routes.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))


@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/get_rooms', methods=['GET'])
@login_required
def get_rooms():
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
               SELECT r.room_id, r.room_name, rp.role_name
               FROM Rooms r
               INNER JOIN RoomParticipants rp ON r.room_id = rp.room_id
               WHERE rp.email = %s;
           """, (current_user.email,))
            user_rooms = [{'id': row[0], 'name': row[1], 'role': row[2]} for row in cur.fetchall()]
            return jsonify(user_rooms)
        except psycopg2.Error as e:
            app.logger.exception(f"Database error getting rooms: {e}")
            return jsonify({'error': f"Ошибка базы данных: {e}"})
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({'error': "Ошибка подключения к базе данных."})
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/room/<room_id>', methods=['GET', 'POST'])
@login_required
def room(room_id):
    # Проверяем, если пользователь уже в комнате (сессия)
    header_form = HeaderForm()
    header_form.email.data = current_user.email
    create_queue_form = CreateQueueForm() #создаем форму

    if f'room_{room_id}_user' in session:
        pass
    else:
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT room_name, room_password, creator_email
                    FROM Rooms
                    WHERE room_id = %s;
                """, (room_id,))

                room_data = cur.fetchone()
                if room_data:
                    room_name, room_password_hash, creator_email = room_data
                    # Проверка, является ли пользователь администратором
                    if current_user.email == creator_email:
                        session[f'room_{room_id}_user'] = current_user.email
                        session[f'room_{room_id}_name'] = room_name
                        session[f'room_{room_id}_id'] = room_id
                        return render_template('room.html', room_id=room_id, room_name=room_name, is_user=False, header_form=header_form, form=create_queue_form)

                    form = RoomPasswordForm()
                    room_password_hash_bytes = bytes(room_password_hash)
                    if form.validate_on_submit():
                        entered_password = form.roomPassword.data
                        username = form.userName.data
                        if bcrypt.checkpw(entered_password.encode('utf-8'), room_password_hash_bytes):
                            session[f'room_{room_id}_user'] = current_user.email
                            session[f'room_{room_id}_name'] = room_name
                            session[f'room_{room_id}_id'] = room_id
                            # Проверяем, если пользователь уже в комнате
                            cur.execute("""
                                    SELECT 1 FROM RoomParticipants
                                    WHERE email = %s AND room_id = %s;
                                """, (current_user.email, room_id))
                            if cur.fetchone() is None:
                                cur.execute("""
                                    INSERT INTO RoomParticipants (email, room_id, role_name, username_in_room)
                                    VALUES (%s, %s, %s, %s);
                                """, (current_user.email, room_id, 'User', username))
                                conn.commit()
                        else:
                           flash("Неправильный пароль", "error")
                           return render_template('room_password.html', room_id=room_id, room_name=room_name, form=form)
                    else:
                        return render_template('room_password.html', room_id=room_id, room_name=room_name, form=form)
                else:
                    flash("Комната не найдена", "error")
                    return redirect(url_for('routes.my_rooms'))
            except psycopg2.Error as e:
                flash(f"Ошибка доступа к комнате: {e}", "error")
                app.logger.exception(f"Database error accessing room: {e}")
                print(f"Database error accessing room: {e}")
                return redirect(url_for('routes.my_rooms'))
            finally:
                cur.close()
                conn.close()
        else:
            flash("Ошибка подключения к базе данных.", "error")
            return redirect(url_for('routes.my_rooms'))
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            # Получение всех очередей (пока без привязки к комнате)
            cur.execute("""
                SELECT queue_id, queue_name
                FROM queues
                WHERE room_id = %s;
            """, (room_id,))
            queues = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
            # Получение пользователей комнаты
            cur.execute("""
                SELECT rp.username_in_room, rp.role_name, rp.email
                FROM RoomParticipants rp
                WHERE rp.room_id = %s;
            """, (room_id,))
            participants = [{'username': row[0], 'role': row[1], 'email': row[2]} for row in cur.fetchall()]
        except psycopg2.Error as e:
            flash(f"Ошибка получения данных: {e}", "error")
            app.logger.exception(f"Database error getting data: {e}")
            queues = []
            participants = []
        finally:
            cur.close()
            conn.close()
    else:
        flash("Ошибка подключения к базе данных.", "error")
        queues = []
        participants = []
    is_user = False
    is_admin = False
    for participant in participants:
        if participant['email'] == current_user.email and participant['role'] == 'User':
            is_user = True
            break
        if participant['email'] == current_user.email and participant['role'] == 'Admin':
            is_admin = True
            break
    form = CreateQueueForm()
    form.roomId.data = room_id #скрытое поле
    return render_template('room.html', room_id=room_id, room_name=session[f'room_{room_id}_name'], queues=queues,
                           participants=participants, is_user=is_user, is_admin=is_admin, header_form=header_form,
                           form=form)

@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/queue/<queue_id>')
@login_required
def queue(queue_id):
    conn = connect_to_db()
    header_form = HeaderForm()  # Инициализация формы для шапки
    header_form.email.data = current_user.email  # Передача email пользователя в форму
    if conn:
        cur = conn.cursor()
        try:
             # Проверка, что очередь существует и получаем данные
            cur.execute("""
                SELECT q.queue_name, q.creation_date, q.available_entries, q.entry_end_time, q.deletion_time, q.room_id, r.creator_email
                FROM queues q
                JOIN Rooms r ON q.room_id = r.room_id
                WHERE q.queue_id = %s;
            """, (queue_id,))
            queue_data = cur.fetchone()
            if not queue_data:
                flash("Очередь не найдена", "error")
                return redirect(url_for('routes.my_rooms'))
            name, creation_date, available_entries, entry_end_time, deletion_time, room_id, creator_email = queue_data
            # Проверка, имеет ли пользователь доступ к комнате
            cur.execute("""
                SELECT 1 FROM RoomParticipants
                WHERE email = %s AND room_id = %s;
            """, (current_user.email, room_id))
            if not cur.fetchone():
                flash("У вас нет доступа к этой очереди", "error")
                return redirect(url_for('routes.my_rooms'))
             # Получаем данные
            creation_date_str = creation_date.strftime('%Y-%m-%d %H:%M:%S') if creation_date else 'Не указано'
            entry_end_time_str = entry_end_time.strftime('%Y-%m-%d %H:%M:%S') if entry_end_time else 'Не указано'
            deletion_time_str = deletion_time.strftime('%Y-%m-%d %H:%M:%S') if deletion_time else 'Не указано'

            cur.execute("""
                SELECT e.entry_id, e.username_in_room, e.creation_date, e.entry_subject, e.is_completed, e.creator_email
                FROM QueueEntries e
                WHERE e.queue_id = %s
                ORDER BY e.creation_date;
            """, (queue_id,))
            queue_entries = [{'id': row[0], 'user_name': row[1], 'created_at': row[2].isoformat(), 'entry_subject': row[3], 'is_completed': row[4], 'user_email': row[5]} for row in cur.fetchall()]
             # Проверяем, является ли пользователь администратором
            is_admin = current_user.email == creator_email
            form = AddEntryForm() #инициализируем форму
            form.queueId.data = queue_id
            return render_template('queue.html', queue_id=queue_id, queue_name=name,
                                   creation_date=creation_date_str, available_entries=available_entries,
                                   entry_end_time=entry_end_time_str, deletion_time=deletion_time_str,
                                   queue_entries=queue_entries, is_admin=is_admin, room_id=room_id, header_form=header_form, form=form)
        except psycopg2.Error as e:
             flash(f"Ошибка получения данных: {e}", "error")
             app.logger.exception(f"Database error getting data: {e}")
             return redirect(url_for('routes.my_rooms'))
        finally:
            cur.close()
            conn.close()
    else:
        flash("Ошибка подключения к базе данных.", "error")
        return redirect(url_for('routes.my_rooms'))
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/complete_entry/<queue_id>/<entry_id>', methods=['POST'])
@login_required
def complete_entry(queue_id, entry_id):
    try:
        is_completed = request.get_json()['is_completed']  # Получаем статус
        conn = connect_to_db()
        cur = conn.cursor()

        # Обновляем статус завершённости записи
        cur.execute("""
            UPDATE QueueEntries
            SET is_completed = %s
            WHERE queue_id = %s AND entry_id = %s;
        """, (is_completed, queue_id, entry_id))
        conn.commit()

        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        app.logger.exception(f"Database error completing entry: {e}")
        return jsonify({'success': False, 'error': str(e)})
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/add_entry/<queue_id>', methods=['POST'])
@login_required

def add_entry(queue_id):
    form = AddEntryForm(request.form)
    if form.validate():
        try:
            entry_subject = form.entrySubject.data  # Текст записи
            conn = connect_to_db()
            cur = conn.cursor()

            # Найти текущее максимальное значение entry_id для этой очереди
            cur.execute("""
                SELECT COALESCE(MAX(entry_id), 0) + 1
                FROM QueueEntries
                WHERE queue_id = %s;
            """, (queue_id,))
            new_entry_id = cur.fetchone()[0]  # Следующий ID для этой очереди

            # Получаем username пользователя в комнате
            cur.execute("""
                SELECT username_in_room
                FROM RoomParticipants
                WHERE email = %s
                  AND room_id = (SELECT room_id FROM queues WHERE queue_id = %s);
            """, (current_user.email, queue_id))
            username_in_room = cur.fetchone()
            if not username_in_room:  # Если имя пользователя в комнате не нашлось
                return jsonify({'success': False, 'error': 'Не удалось найти имя пользователя в комнате'})

            # Добавить новую запись в очередь
            cur.execute("""
                INSERT INTO QueueEntries (entry_id, queue_id, creator_email, username_in_room, creation_date, entry_subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING entry_id;
            """, (new_entry_id, queue_id, current_user.email, username_in_room[0], datetime.now(), entry_subject))
            conn.commit()

            # Возвращаем новый entry_id
            entry_id = cur.fetchone()[0]
            cur.close()
            conn.close()
            return jsonify({'success': True, 'entryId': entry_id})
        except Exception as e:
            app.logger.exception(f"Database error adding entry: {e}")
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': form.errors})
@routes.before_request
def clear_flashes():
    session.pop('_flashes', None)
@routes.route('/get_queues', methods=['GET'])
@login_required
def get_queues():
    room_id = request.args.get('roomId')
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
               SELECT queue_id, queue_name
                FROM queues
                WHERE room_id = %s;
            """, (room_id,))
            queues = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
            return jsonify(queues)
        except psycopg2.Error as e:
            app.logger.exception(f"Database error getting queues: {e}")
            return jsonify({'error': f"Ошибка базы данных: {e}"})
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({'error': "Ошибка подключения к базе данных."})


@routes.route('/delete_queue/<queue_id>', methods=['POST'])
@login_required
def delete_queue(queue_id):
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Ошибка подключения к базе данных'})

        cur = conn.cursor()
        try:
            # Получаем ID комнаты и проверяем права администратора
            cur.execute("""
                SELECT q.room_id, r.creator_email
                FROM Queues q
                INNER JOIN Rooms r ON q.room_id = r.room_id
                WHERE q.queue_id = %s;
            """, (queue_id,))
            result = cur.fetchone()

            if not result:
                return jsonify({'success': False, 'error': 'Очередь не найдена'})

            room_id, creator_email = result

            if creator_email != current_user.email:
                return jsonify({'success': False, 'error': 'Только администратор может удалять эту очередь'})

            # Удаляем записи в очереди и саму очередь
            cur.execute("DELETE FROM QueueEntries WHERE queue_id = %s;", (queue_id,))
            cur.execute("DELETE FROM Queues WHERE queue_id = %s;", (queue_id,))

            conn.commit()
            return jsonify(
                {'success': True, 'redirect_url': url_for('routes.room', room_id=room_id)})  # Возвращаем URL комнаты
        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': f'Ошибка базы данных: {e}'})
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@routes.route('/delete_room/<room_id>', methods=['DELETE'])
@login_required
def delete_room(room_id):
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            # Проверить, является ли пользователь администратором комнаты.
            cur.execute("""
                SELECT creator_email FROM Rooms WHERE room_id = %s;
            """, (room_id,))
            creator_email = cur.fetchone()

            if not creator_email or creator_email[0] != current_user.email:
                return jsonify(
                    {'success': False, 'error': 'Доступ запрещен. Только администратор может удалять комнату.'}), 403

            # Удалить связанные очереди и участников
            cur.execute("""
                DELETE FROM QueueEntries WHERE room_id = %s;
                DELETE FROM Queues WHERE room_id = %s;
                DELETE FROM RoomParticipants WHERE room_id = %s;
                DELETE FROM Rooms WHERE room_id = %s;
            """, (room_id, room_id, room_id, room_id))
            conn.commit()

            return jsonify({'success': True, 'message': 'Комната успешно удалена.'})
        except psycopg2.Error as e:
            conn.rollback()
            app.logger.exception(f"Database error during room deletion: {e}")
            return jsonify({'success': False, 'error': 'Ошибка базы данных.'}), 500
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Ошибка подключения к базе данных.'}), 500
