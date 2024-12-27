import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '336c8e1b3598c552b1b672b42e1271d04357c3a09d550eb83c609b512acc875b'
    DB_USER = os.environ.get('POSTGRES_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or 'o1NVGP3kDR5r3bH7'
    DB_HOST = os.environ.get('POSTGRES_HOST') or 'modestly-tangible-skylark.data-1.use1.tembo.io'
    DB_PORT = os.environ.get('POSTGRES_PORT') or '5432'
    DB_NAME = os.environ.get('POSTGRES_DB') or 'postgres'
