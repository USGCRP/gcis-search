import os, sys, json, requests, traceback
from datetime import datetime

from flask import Blueprint, request, redirect, url_for, Response, current_app
from flask.ext.restplus import Api, apidoc, Resource, fields
from flask.ext.login import login_user, logout_user, login_required

from fv_prov_es import cache
from fv_prov_es.lib.utils import get_prov_es_json, get_ttl
from fv_prov_es.lib.import_utils import get_es_conn, import_prov


NAMESPACE = "prov_es"

services = Blueprint('api_v0-1', __name__, url_prefix='/api/v0.1')
api = Api(services, ui=False, version="0.1", title="PROV-ES API",
          description="API for ingest, query, and visualization of PROV-ES documents")
ns = api.namespace(NAMESPACE, description="PROV-ES operations")


@services.route('/doc/', endpoint='doc')
def swagger_ui():
    return apidoc.ui_for(api)


@ns.route('/query', endpoint='query')
@api.doc(responses={ 200: "Success",
                     400: "Invalid parameters",
                     500: "Query execution failed" },
         description="Query PROV-ES ElasticSearch index and return results as a JSONP response.")
class Query(Resource):
    """Query ElasticSearch index and return results as a JSONP response."""

    @api.doc(params={ 'callback': 'JSONP callback function name',
                      'source'  : 'JSON query source string'})
    def get(self):
        # get callback, source
        callback = request.args.get('callback', None)
        if callback is None:
            return {'success': False,
                    'message': "Missing callback parameter."}, 400
        source = request.args.get('source', None)
        if source is None:
            return {'success': False,
                    'message': "Missing source parameter."}, 400
    
        # query
        es_url = current_app.config['ES_URL']
        es_index = current_app.config['PROVES_ES_ALIAS']
        #current_app.logger.debug("ES query for query(): %s" % json.dumps(json.loads(source), indent=2))
        r = requests.post('%s/%s/_search' % (es_url, es_index), data=source.encode('utf-8'))
        result = r.json()
        if r.status_code != 200:
            message = "Failed to query ES. Got status code %d:\n%s" % \
                      (r.status_code, json.dumps(result, indent=2))
            current_app.logger.debug(message)
            return {'success': False, 'message': message}, 500
        #current_app.logger.debug("result: %s" % pformat(r.json()))
    
        # return only one url
        for hit in result['hits']['hits']:
            # emulate result format from ElasticSearch <1.0
            #current_app.logger.debug("hit: %s" % pformat(hit))
            if '_source' in hit: hit.setdefault('fields', {}).update(hit['_source'])
            hit['fields']['_type'] = hit['_type']
    
        # return JSONP
        return Response('%s(%s)' % (callback, json.dumps(result)),
                        mimetype="application/javascript")


@ns.route('/json', endpoint='prov_es_json')
@api.doc(responses={ 200: "Success",
                     400: "Invalid parameters",
                     500: "Query execution failed" },
         description="Get PROV-ES document by ID and return as JSON.")
class QueryJson(Resource):
    """Get PROV-ES document by ID and return as JSON."""

    resp_model = api.model('JsonResponse', {
        'success': fields.Boolean(required=True, description="if 'false', encountered exception; otherwise no errors occurred"),
        'message': fields.String(required=True, description="message describing success or failure"),
        'result':  fields.Raw(required=True, description="PROV-ES JSON document")
    })

    @api.doc(params={ 'id': 'ID of PROV-ES document'})
    @api.marshal_with(resp_model)
    def get(self):
        id = request.args.get('id', None)
        if id is None:
            return { 'success': False,
                     'message': "Missing id parameter.",
                     'result': {} }, 400
    
        # query
        try: pej = get_prov_es_json(id)
        except Exception, e:
            message = "Failed to get PROV-ES document for id %s: %s" % (id, str(e))
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': {} }, 500

        # set message
        if len(pej) == 0: message = "No document found with id %s." % id
        else: message = ""

        # return result
        return { 'success': True,
                 'message': message,
                 'result': pej.get('_source', {}) }


@services.route('/%s/download/json' % NAMESPACE,
                endpoint="download_prov_es_json", methods=['GET'])
def download_prov_es_json():
    """Download lineage."""

    # get id
    id = request.args.get('id', None)
    if id is None:
        return jsonify({
            'success': False,
            'message': "No id specified."
        }), 500

    pej = get_prov_es_json(id)
    if pej is None:
        return jsonify({
            'success': False,
            'message': "No document found with id %s." % id
        }), 500
    response = Response(json.dumps(pej['_source']['prov_es_json'], indent=2))
    response.headers["Content-Disposition"] = "attachment; filename=prov_es.json"
    return response


@ns.route('/ttl', endpoint='prov_es_ttl')
@api.doc(responses={ 200: "Success",
                     400: "Invalid parameters",
                     500: "Query execution failed" },
         description="Get PROV-ES document by ID and return as Turtle.")
class QueryTurtle(Resource):
    """Get PROV-ES document by ID and return as Turtle."""

    resp_model = api.model('TurtleResponse', {
        'success': fields.Boolean(required=True, description="if 'false', encountered exception; otherwise no errors occurred"),
        'message': fields.String(required=True, description="message describing success or failure"),
        'result':  fields.String(required=True, description="PROV-ES Turtle document")
    })

    @api.doc(params={ 'id': 'ID of PROV-ES document'})
    @api.marshal_with(resp_model)
    def get(self):
        id = request.args.get('id', None)
        if id is None:
            return { 'success': False,
                     'message': "Missing id parameter.",
                     'result': "" }, 400
    
        # query
        try: pej = get_prov_es_json(id)
        except Exception, e:
            message = "Failed to get PROV-ES document for id %s: %s" % (id, str(e))
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': "" }, 500

        # if no document found, return
        if len(pej) == 0:
            message = "No PROV-ES document found with id %s." % id
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': "" }, 500

        # convert PROV-ES JSON to turtle
        try: ttl = get_ttl(pej['_source']['prov_es_json'])
        except Exception, e:
            message = "Failed to transform PROV-ES JSON document to Turtle for id %s: %s" % (id, str(e))
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': "" }, 500

        # return result
        return { 'success': True,
                 'message': "",
                 'result': ttl }


@services.route('/%s/download/ttl' % NAMESPACE,
                endpoint="download_prov_es_ttl", methods=['GET'])
def download_prov_es_ttl():

    # get id
    id = request.args.get('id', None)
    if id is None:
        return jsonify({
            'success': False,
            'message': "No id specified."
        }), 500

    # return turtle
    j = get_prov_es_json(id)
    ttl = get_ttl(j['_source']['prov_es_json'])
    response = Response(ttl)
    response.headers["Content-Disposition"] = "attachment; filename=prov_es.ttl"
    return response


SAMPLE_PROV_ES_JSON = """{
  "prefix": {
    "info": "http://info-uri.info/", 
    "bibo": "http://purl.org/ontology/bibo/", 
    "hysds": "http://hysds.jpl.nasa.gov/hysds/0.1#", 
    "ex1": "http://example.org/my_namespace#", 
    "xlink": "http://www.w3.org/1999/xlink", 
    "eos": "http://nasa.gov/eos.owl#", 
    "gcis": "http://data.globalchange.gov/gcis.owl#", 
    "dcterms": "http://purl.org/dc/terms/"
  }, 
  "used": {
    "ex1:used-file-1": {
      "prov:role": "input",
      "prov:time": "2015-03-22T16:07:05.195235+00:00", 
      "prov:entity": "ex1:file-1",
      "prov:activity": "ex1:my-md5sum-activity"
    }
  }, 
  "agent": {
    "ex1:my-software-agent": {
      "hysds:host": "mimosa-vm-3.jpl.nasa.gov", 
      "prov:type": {
        "type": "prov:QualifiedName", 
        "$": "prov:SoftwareAgent"
      }, 
      "hysds:pid": "1921"
    }
  }, 
  "entity": {
    "ex1:file-1": {
      "prov:location": "http://path/to/my/input-file",
      "prov:type": {
        "type": "prov:QualifiedName",
        "$": "eos:granule"
      }
    }, 
    "ex1:md5sum-file": {
      "prov:location": "http://path/to/my/output-file",
      "prov:type": {
        "type": "prov:QualifiedName",
        "$": "eos:product"
      }
    }
  }, 
  "activity": {
    "ex1:my-md5sum-activity": {
      "prov:wasAssociatedWith": "ex1:my-software-agent",
      "prov:label": "md5sum command",
      "prov:startTime": "2015-03-22T14:55:43.906447+00:00", 
      "prov:type": {
        "type": "prov:QualifiedName",
        "$": "eos:processStep"
      },
      "prov:endTime": "2015-03-22T14:56:43.906447+00:00"
    }
  }, 
  "wasAssociatedWith": {
    "hysds:my-activity-agent-association": {
      "prov:role": "softwareAgent",
      "prov:agent": "ex1:my-software-agent",
      "prov:activity": "ex1:my-md5sum-activity"
    }
  },
  "wasGeneratedBy": {
    "ex1:generated-md5sum-file": {
      "prov:role": "output",
      "prov:time": "2015-03-22T14:56:43.906447+00:00",
      "prov:entity": "ex1:md5sum-file",
      "prov:activity": "ex1:my-md5sum-activity"
    }
  }
}"""


@ns.route('/import/json', endpoint='import_prov_es')
@api.doc(responses={ 200: "Success",
                     400: "Invalid parameters",
                     500: "Import execution failed" },
         description="Import PROV-ES document. To test it, " +
                     "copy and paste the following PROV-ES " +
                     "JSON into the PROV-ES textbox below:\n" +
                     "<pre>%s</pre>" % SAMPLE_PROV_ES_JSON)
class ImportProvEs(Resource):
    """Import PROV-ES document."""

    resp_model = api.model('ImportResponse', {
        'success': fields.Boolean(required=True, description="if 'false', encountered exception; otherwise no errors occurred"),
        'message': fields.String(required=True, description="message describing success or failure")
    })

    @api.doc(params={ 'prov_es': 'PROV-ES JSON document string'})
    @api.marshal_with(resp_model)
    def post(self):
        # get PROV-ES json
        prov_es = request.form.get('prov_es', request.args.get('prov_es', None))
        if prov_es is None:
            return { 'success': False,
                     'message': "Missing prov_es parameter.",
                     'result': {} }, 400

        # load JSON
        try: pej = json.loads(prov_es)
        except Exception, e:
            message = "Failed to parse PROV-ES json. Check that your PROV-ES JSON conforms to PROV-JSON."
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': {} }, 500

        # import prov
        es_url = current_app.config['ES_URL']
        dt = datetime.utcnow()
        es_index = "%s-%04d.%02d.%02d" % (current_app.config['PROVES_ES_PREFIX'],
                                          dt.year, dt.month, dt.day)
        alias = current_app.config['PROVES_ES_ALIAS']
        conn = get_es_conn(es_url, es_index, alias)
        try: import_prov(conn, es_index, alias, pej)
        except Exception, e:
            current_app.logger.debug("Got error: %s" % e)
            current_app.logger.debug("Traceback: %s" % traceback.format_exc())
            message = "Failed to import PROV-ES json. Check that your PROV-ES JSON conforms to PROV-JSON."
            current_app.logger.debug(message)
            return { 'success': False,
                     'message': message,
                     'result': {} }, 500

        # return result
        return { 'success': True,
                 'message': "" }
