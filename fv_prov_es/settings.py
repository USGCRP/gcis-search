class Config(object):
    SECRET_KEY = 'secret key'
    ES_URL = 'http://127.0.0.1:5001' # default port is 9200

    # for PROVES app
    PROVES_ES_PREFIX = 'prov_es'
    PROVES_ES_ALIAS = 'prov_es'

    # ES template
    ES_TEMPLATE = "../config/es_template-prov_es.json"


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'

    CACHE_TYPE = 'null'


class DevConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'
    SQLALCHEMY_ECHO = True

    CACHE_TYPE = 'null'

    # This allows us to test the forms from WTForm
    WTF_CSRF_ENABLED = False

    # for PROVES app
    PROVES_ES_PREFIX = 'prov_es_dev'
