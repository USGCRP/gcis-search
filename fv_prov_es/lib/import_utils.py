import os, sys, json, requests, copy, types
from pyes import ES, TermQuery
from pyes.exceptions import SearchPhaseExecutionException
from flask import current_app

from prov_es.model import get_uuid


def get_es_conn(es_url, index, alias=None):
    """Create connection and create index if it doesn't exist."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index)
        if alias is not None:
            conn.indices.add_alias(alias, [index])
    return conn


def fix_hadMember_ids(prov_es_json):
    """Fix the id's of hadMember relationships."""

    hm_ids = prov_es_json.get('hadMember', {}).keys()
    for id in hm_ids:
        hm = copy.deepcopy(prov_es_json['hadMember'][id])
        new_id = "hysds:%s" % get_uuid("%s:%s" % (hm['prov:collection'], hm['prov:entity']))
        prov_es_json['hadMember'][new_id] = hm
        del prov_es_json['hadMember'][id]


def import_prov(conn, index, alias, prov_es_json):
    """Index PROV-ES concepts into ElasticSearch."""

    # fix hadMember ids
    fix_hadMember_ids(prov_es_json)
    #print(json.dumps(prov_es_json, indent=2))

    # import
    prefix = prov_es_json['prefix']
    for concept in prov_es_json:
        if concept == 'prefix': continue
        elif concept == 'bundle':
            for bundle_id in prov_es_json['bundle']:
                try:
                    found = len(conn.search(query=TermQuery("_id", bundle_id),
                                            indices=[alias]))
                except SearchPhaseExecutionException:
                    found = 0
                if found > 0: continue
                bundle_prov = copy.deepcopy(prov_es_json['bundle'][bundle_id])
                bundle_prov['prefix'] = prefix
                bundle_doc = {
                    'identifier': bundle_id,
                    'prov_es_json': bundle_prov,
                }
                for b_concept in bundle_prov:
                    if b_concept == 'prefix': continue
                    bundle_doc[b_concept] = []
                    for i in bundle_prov[b_concept]:
                        doc = copy.deepcopy(bundle_prov[b_concept][i])
                        prov_doc = copy.deepcopy(doc)
                        doc['identifier'] =  i
                        doc['prov_es_json'] = { 'prefix': prefix }
                        doc['prov_es_json'].setdefault(b_concept, {})[i] = prov_doc
                        if 'prov:type' in doc and isinstance(doc['prov:type'], types.DictType):
                            doc['prov:type'] = doc['prov:type'].get('$', '')
                        try:
                            found = len(conn.search(query=TermQuery("_id", i),
                                                    indices=[alias]))
                        except SearchPhaseExecutionException:
                            found = 0
                        if found > 0: pass
                        else: conn.index(doc, index, b_concept, i)
                        bundle_doc[b_concept].append(i)
                conn.index(bundle_doc, index, 'bundle', bundle_id)
        else:
            for i in prov_es_json[concept]:
                try:
                    found = len(conn.search(query=TermQuery("_id", i),
                                            indices=[alias]))
                except SearchPhaseExecutionException:
                    found = 0
                if found > 0: continue
                docs = prov_es_json[concept][i]
                if not isinstance(docs, types.ListType): docs = [docs]
                for doc in docs:
                    prov_doc = copy.deepcopy(doc)
                    doc['identifier'] =  i
                    doc['prov_es_json'] = { 'prefix': prefix }
                    doc['prov_es_json'].setdefault(concept, {})[i] = prov_doc
                    if 'prov:type' in doc and isinstance(doc['prov:type'], types.DictType):
                        doc['prov:type'] = doc['prov:type'].get('$', '')
                    conn.index(doc, index, concept, i)
