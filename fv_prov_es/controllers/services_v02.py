import os, sys, json, requests

from flask import Blueprint, request, redirect, url_for, Response, current_app
from flask.ext.restplus import Api, apidoc, Resource, fields
from flask.ext.login import login_user, logout_user, login_required

from fv_prov_es import cache
from fv_prov_es.lib.utils import get_prov_es_json, get_ttl


NAMESPACE = "prov_es"

services = Blueprint('api_v0-2', __name__, url_prefix='/api/v0.2')
api = Api(services, ui=False, version="0.2", title="PROV-ES API",
          description="API for ingest, query, and visualization of PROV-ES documents")
ns = api.namespace(NAMESPACE, description="PROV-ES operations")


@services.route('/doc/', endpoint='doc')
def swagger_ui():
    return apidoc.ui_for(api)
