#!/usr/bin/env python
import os, sys, json, requests, types, re, copy
from datetime import datetime
import requests_cache

from fv_prov_es import create_app
from fv_prov_es.lib.import_utils import get_es_conn, import_prov

from prov_es.model import (get_uuid, ProvEsDocument, GCIS, PROV, PROV_TYPE,
    PROV_ROLE, PROV_LABEL, PROV_LOCATION, HYSDS)


requests_cache.install_cache('gcis-import')


journal_ids = {}

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
    if journal_id not in journal_ids:
        if journal_md.get('url', None) is not None:
            doc_attrs.append( ("prov:location", journal_md['url'] ) )
        if journal_md.get('online_issn', None) is not None:
            doc_attrs.append( ("gcis:online_issn", journal_md['online_issn'] ) )
        if journal_md.get('print_issn', None) is not None:
            doc_attrs.append( ("gcis:print_issn", journal_md['print_issn'] ) )
        doc.entity(journal_id, doc_attrs)
        journal_ids[journal_id] = True

    # create agents or organizations
    agent_ids = {}
    org_ids = {}
    for cont in j.get('contributors', []):
        # replace slashes because we get prov.model.ProvExceptionInvalidQualifiedName errors
        agent_id = GCIS["%s" % cont['uri'][1:].replace('/', '-')]

        # create person
        if len(cont['person']) > 0:
            # agent 
            agent_name  = " ".join([cont['person'][i] for i in
                                    ('first_name', 'middle_name', 'last_name')
                                    if cont['person'].get(i, None) is not None])
            doc.agent(agent_id, [
                ( PROV_TYPE, GCIS["Person"] ),
                ( PROV_LABEL, agent_name ),
                ( PROV_LOCATION, "%s%s" % (gcis_url, cont['uri']) ),
            ])
            agent_ids[agent_id] = []

        # organization
        if cont['organization'] is not None and len(cont['organization']) > 0:
            org = cont['organization']
            org_id = GCIS["%s" % cont['organization']['identifier']]
            if org_id not in org_ids:          
                doc.governingOrganization(org_id, cont['organization']['name'])
                org_ids[org_id] = True
            if agent_id in agent_ids: agent_ids[agent_id].append(org_id)

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

    # create activity
    if isinstance(j['year'], int):
        start_time = str(j['year'])
        end_time = str(j['year'])
    else:
        start_time = None
        end_time = None
    act_id = GCIS["generate-%s" % j['identifier'].replace('/', '-')]
    attrs = []
    for agent_id in agent_ids:
        waw_id = GCIS["%s" % get_uuid("%s:%s" % (act_id, agent_id))]
        doc.wasAssociatedWith(act_id, agent_id, None, waw_id, {'prov:role': GCIS['Author']})
        for org_id in agent_ids[agent_id]:
            del_id = GCIS["%s" % get_uuid("%s:%s:%s" % (agent_id, org_id, act_id))]
            doc.delegation(agent_id, org_id, act_id, del_id, {'prov:type': 'gcis:worksAt'})
    for org_id in org_ids:
        waw_id = GCIS["%s" % get_uuid("%s:%s" % (act_id, org_id))]
        doc.wasAssociatedWith(act_id, org_id, None, waw_id, {'prov:role': GCIS['Contributor']})
    act = doc.activity(act_id, start_time, end_time, attrs)
    doc.wasGeneratedBy(article_id, act, end_time, GCIS["%s" % get_uuid("%s:%s" % (article_id, act_id))])

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
