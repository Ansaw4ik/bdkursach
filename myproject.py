from flask import Flask, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from app.routes import routes as route_blueprint, connect_to_db
from app import config
from app.models import User

app = Flask(__name__, template_folder='./app/templates', static_folder='./app/static') # Указали путь к папке templates
app.config.from_object(config.Config)
app.register_blueprint(route_blueprint, url_prefix='/')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.login'

@login_manager.user_loader
def load_user(user_email):
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT email FROM users WHERE email = %s", (user_email,))
            user = cur.fetchone()
            if user:
                return User(user[0])
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    return None

if __name__ == '__main__':
    app.run(debug=True)

