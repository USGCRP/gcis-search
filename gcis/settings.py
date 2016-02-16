class Config(object):
    SECRET_KEY = 'secret key'
    #GCIS_REST_URL = 'http://127.0.0.1:3000'
    GCIS_REST_URL = 'http://data.globalchange.gov'
    ELASTICSEARCH_URL = 'http://127.0.0.1:9200'

    # for GCIS app
    GCIS_ELASTICSEARCH_INDEX = 'gcis'
    GCIS_ELASTICSEARCH_SETTINGS = '../config/es_settings-gcis.json'
    GCIS_ELASTICSEARCH_MAPPING = '../config/es_mapping-gcis.json'

    # CEOS-GCMD merged instruments/platforms app
    CEOS_GCMD_ELASTICSEARCH_INDEX = 'ceos_gcmd'
    CEOS_GCMD_ELASTICSEARCH_SETTINGS = '../config/es_settings-ceos_gcmd.json'
    CEOS_GCMD_ELASTICSEARCH_MAPPING = '../config/es_mapping-ceos_gcmd.json'

class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'

    CACHE_TYPE = 'simple'


class DevConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'
    SQLALCHEMY_ECHO = True

    CACHE_TYPE = 'null'

    # This allows us to test the forms from WTForm
    WTF_CSRF_ENABLED = False
