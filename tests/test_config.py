#! ../env/bin/python
# -*- coding: utf-8 -*-
<<<<<<< HEAD
from fv_prov_es import create_app
=======
from gcis import create_app
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9


class TestConfig:
    def test_dev_config(self):
<<<<<<< HEAD
        app = create_app('fv_prov_es.settings.DevConfig', env='dev')
=======
        app = create_app('gcis.settings.DevConfig', env='dev')
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9

        assert app.config['DEBUG'] is True
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///../database.db'
        assert app.config['SQLALCHEMY_ECHO'] is True
        assert app.config['CACHE_TYPE'] == 'null'

    def test_prod_config(self):
<<<<<<< HEAD
        app = create_app('fv_prov_es.settings.ProdConfig', env='prod')
=======
        app = create_app('gcis.settings.ProdConfig', env='prod')
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9

        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///../database.db'
        assert app.config['CACHE_TYPE'] == 'simple'
