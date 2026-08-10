import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE = os.path.join(basedir, 'instance', 'app.db')
    WTF_CSRF_ENABLED = True


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


config = {
    'development': DevConfig,
    'production': ProdConfig,
    'default': DevConfig,
}
