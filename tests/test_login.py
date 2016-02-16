#! ../env/bin/python
# -*- coding: utf-8 -*-
<<<<<<< HEAD
from fv_prov_es import create_app
from fv_prov_es.models import db, User
=======
from gcis import create_app
from gcis.models import db, User
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9


class TestForm:
    def setup(self):
<<<<<<< HEAD
        app = create_app('fv_prov_es.settings.DevConfig', env='dev')
=======
        app = create_app('gcis.settings.DevConfig', env='dev')
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9
        self.app = app.test_client()
        db.app = app
        db.create_all()
        admin = User('admin', 'supersafepassword')
        db.session.add(admin)
        db.session.commit()

    def teardown(self):
        db.session.remove()
        db.drop_all()

    def test_user_login(self):
        rv = self.app.post('/login', data=dict(
            username='admin',
            password="supersafepassword"
        ), follow_redirects=True)

        assert rv.status_code == 200
        assert 'Logged in successfully.' in rv.data
