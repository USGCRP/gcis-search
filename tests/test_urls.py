#! ../env/bin/python
# -*- coding: utf-8 -*-
<<<<<<< HEAD
from fv_prov_es import create_app
from fv_prov_es.models import db
=======
from gcis import create_app
from gcis.models import db
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9


class TestURLs:
    def setup(self):
<<<<<<< HEAD
        app = create_app('fv_prov_es.settings.DevConfig', env='dev')
=======
        app = create_app('gcis.settings.DevConfig', env='dev')
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9
        self.app = app.test_client()
        db.app = app
        db.create_all()

    def teardown(self):
        db.session.remove()
        db.drop_all()

    def test_home(self):
        rv = self.app.get('/')
        assert rv.status_code == 200

    def test_login(self):
        rv = self.app.get('/login')
        assert rv.status_code == 200

    def test_logout(self):
        rv = self.app.get('/logout')
        assert rv.status_code == 302

    def test_restricted(self):
        rv = self.app.get('/restricted')
        assert rv.status_code == 302
