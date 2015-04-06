#!/usr/bin/env python
import os, sys, json, requests
from jinja2 import Template

from fv_prov_es import create_app


def write_template(es_url, prefix, alias, tmpl_file):
    """Write template to ES."""

    with open(tmpl_file) as f:
        tmpl = Template(f.read()).render(prefix=prefix, alias=alias)
    tmpl_url = "%s/_template/%s" % (es_url, alias)
    r = requests.put(tmpl_url, data=tmpl)
    r.raise_for_status()
    print r.json()
    print "Successfully installed template %s at %s/_templ." % (alias, tmpl_url)


if __name__ == "__main__":
    env = os.environ.get('PROVES_ENV', 'prod')
    app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ES_URL']
    prefix = app.config['PROVES_ES_PREFIX']
    alias = app.config['PROVES_ES_ALIAS']
    tmpl_file = os.path.normpath(os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'config', 'es_template-prov_es.json'
    )))
    write_template(es_url, prefix, alias, tmpl_file)
