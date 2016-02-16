#! ../env/bin/python
# -*- coding: utf-8 -*-
<<<<<<< HEAD
from fv_prov_es import create_app
from fv_prov_es.models import db, User
=======
from gcis import create_app
from gcis.models import db, User
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9


class TestModels:
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

    def test_user(self):
        admin = User('admin', 'supersafepassword')

        assert admin.username == 'admin'
        assert admin.password == 'supersafepassword'

        db.session.add(admin)
        db.session.commit()
