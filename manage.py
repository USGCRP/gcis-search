#!/usr/bin/env python
import os

from flask.ext.script import Manager, Server
<<<<<<< HEAD
from fv_prov_es import create_app
from fv_prov_es.models import db, User

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('PROVES_ENV', 'dev')
app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
=======
from gcis import create_app
from gcis.models import db, User

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('GCIS_ENV', 'dev')
app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9

manager = Manager(app)
manager.add_command("server", Server())


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
        in the context of the app
    """

    return dict(app=app, db=db, User=User)


@manager.command
def createdb():
    """ Creates a database with all of the tables defined in
        your Alchemy models
    """

    db.create_all()

if __name__ == "__main__":
    manager.run()
