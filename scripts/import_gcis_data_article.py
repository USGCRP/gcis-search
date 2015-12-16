#!/usr/bin/env python
import os, sys, json, requests, types, re, copy
from datetime import datetime
import requests_cache

from fv_prov_es import create_app
from fv_prov_es.lib.import_utils import get_es_conn, import_prov

from prov_es.model import get_uuid, ProvEsDocument, GCIS


requests_cache.install_cache('gcis-import')


JOURNALS = {}

def get_doc_prov(j, gcis_url):
    """Generate PROV-ES JSON from GCIS doc metadata."""

    # create doc
    gcis_ns = "http://data.globalchange.gov/gcis.owl#"
    doc = ProvEsDocument(namespaces={ "gcis": gcis_ns, "bibo": "http://purl.org/ontology/bibo/" })
    bndl = None

    # create journal
    r = requests.get("%s/journal/%s.json" % (gcis_url, j['journal_identifier']), params={ 'all': 1 }, verify=False)
    r.raise_for_status()
    journal_md = r.json()
    doc_attrs = [
        ( "prov:type", 'gcis:Journal' ),
        ( "prov:label", j['title'] ),
    ]
    journal_id = GCIS[j['journal_identifier']]
    if journal_id not in JOURNALS:
        if journal_md.get('url', None) is not None:
            doc_attrs.append( ("prov:location", journal_md['url'] ) )
        if journal_md.get('online_issn', None) is not None:
            doc_attrs.append( ("gcis:online_issn", journal_md['online_issn'] ) )
        if journal_md.get('print_issn', None) is not None:
            doc_attrs.append( ("gcis:print_issn", journal_md['print_issn'] ) )
        doc.entity(journal_id, doc_attrs)
        JOURNALS[journal_id] = True

    # create article
    article_id = 'bibo:%s' % j['identifier']
    doc_attrs = [
        ( "prov:type", 'gcis:Article' ),
        ( "prov:label", j['title'] ),
        ( "dcterms:isPartOf", journal_id ),
    ]
    if j.get('doi', "") == "": 
        doc_attrs.append( ("bibo:doi", j['doi'] ) )
    doc.entity(article_id, doc_attrs)

    # link
    doc.hadMember(journal_id, article_id)
           
    # serialize
    prov_json = json.loads(doc.serialize())

    return prov_json


def index_gcis(gcis_url, es_url, index, alias):
    """Index GCIS into PROV-ES ElasticSearch index."""

    conn = get_es_conn(es_url, index, alias)
    r = requests.get('%s/article.json' % gcis_url, params={ 'all': 1 }, verify=False)
    r.raise_for_status()
    docs = r.json()
    #print(json.dumps(images, indent=2))
    #print(len(images))
    for doc in docs:
        doc_id = doc['identifier']
        doc_href = doc['href']
        r2 = requests.get(doc_href, params={ 'all': 1 }, verify=False)
        r2.raise_for_status()
        doc_md = r2.json()
        #print(json.dumps(doc_md, indent=2))
        prov = get_doc_prov(doc_md, gcis_url)
        #print(json.dumps(prov, indent=2))
        import_prov(conn, index, alias, prov)


if __name__ == "__main__":
    env = os.environ.get('PROVES_ENV', 'prod')
    app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ES_URL']
    #gcis_url =  "http://data.globalchange.gov"
    gcis_url =  "https://gcis-search-stage.jpl.net:3000"
    dt = datetime.utcnow()
    #index = "%s-%04d.%02d.%02d" % (app.config['PROVES_ES_PREFIX'],
    #                               dt.year, dt.month, dt.day)
    index = "%s-gcis" % app.config['PROVES_ES_PREFIX']
    alias = app.config['PROVES_ES_ALIAS']
    index_gcis(gcis_url, es_url, index, alias)
