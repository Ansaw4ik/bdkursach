from flask import Flask
from app.config import Config
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__)
app.config.from_object(Config)
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)
from app import routes
