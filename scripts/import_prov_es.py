#!/usr/bin/env python
import os, sys, json, requests, copy, hashlib, re
from datetime import datetime
from pyes import ES
from urlparse import urlparse

from hysds.recognize import Recognizer

from fv_prov_es import create_app


file_url_re = re.compile(r'^file://(.*?)/data/work/(.+)$')

es_url = "http://bellini-vm-1.jpl.nasa.gov:9200"
index = "grq_dev"
scroll_search_tmpl = "%s/%s/_search?search_type=scan&scroll=10m&size=100"
scroll_tmpl = "%s/_search/scroll?scroll=10m"

scroll_search_url = scroll_search_tmpl % (es_url, index)
scroll_url = scroll_tmpl % es_url

query = {
    "query": {
        "match_all": {}
    }
}

# collect all product urls
r = requests.post(scroll_search_url, data=json.dumps(query))
r.raise_for_status()
scroll_id = r.json()['_scroll_id']
prod_urls = []
while True:
    r = requests.post(scroll_url, data=scroll_id)
    res = r.json()
    scroll_id = res['_scroll_id']
    if len(res['hits']['hits']) == 0: break
    for hit in res['hits']['hits']:
        prod_urls.append(hit['_source']['urls'][0])

# get prod or dev env
env = os.environ.get('PROVES_ENV', 'prod')
app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)

# get datetime
dt = datetime.utcnow()

# import into ES
es_url = app.config['ES_URL']
index = "%s-%04d.%02d.%02d" % (app.config['PROVES_ES_PREFIX'],
                               dt.year, dt.month, dt.day)
conn = ES(es_url)
if not conn.indices.exists_index(index):
    conn.indices.create_index(index)
    
# collect prov_es json for all products and index
for prod_url in prod_urls:
    # check for prov_es.json
    prov_es_url = "%s/prov_es.json" % prod_url
    r2 = requests.get(prov_es_url)
    if r2.status_code == 404: continue # skip those without provenance
    r2.raise_for_status()
    prov_es_json = r2.json()
    #print(json.dumps(prov_es_json, indent=2))

    # if downloadURL basename found in prod_url, overwrite downloadURL with prod_url
    for k in prov_es_json['wasGeneratedBy']:
        ent_key = prov_es_json['wasGeneratedBy'][k]['prov:entity']
        entity_doc = prov_es_json['entity'][ent_key]
        if 'gcis:downloadURL' in entity_doc:
            dl_url = entity_doc['gcis:downloadURL']
            if dl_url.startswith('file://'):
                parsed_url = urlparse(dl_url)
                try:
                    r = Recognizer(app.config['DATASETS'], parsed_url.path)
                    entity_doc['gcis:downloadURL'] = r.getPublishUrls()[0]
                except OSError:
                    entity_doc['gcis:downloadURL'] = prod_url
    
    # parse prov:Agent docs
    agent_docs = {}
    for k in prov_es_json['agent']:
        agent_doc = copy.deepcopy(prov_es_json['agent'][k])
        agent_doc['identifier'] = k
        agent_doc['id'] = hashlib.md5(k).hexdigest()
        es_concept = agent_doc['prov:type']['$']
        agent_doc['prov:concept'] = es_concept
        del agent_doc['prov:type']
        if es_concept == 'prov:SoftwareAgent':
            agent_doc['prov:type'] = 'eos:softwareAgent'
        else:
            agent_doc['prov:type'] = es_concept
        agent_docs[k] = agent_doc
    
    #print(json.dumps(agent_docs, indent=2))
    
    
    # parse prov:Entity docs
    entity_docs = {}
    for k in prov_es_json['entity']:
        entity_doc = copy.deepcopy(prov_es_json['entity'][k])
        if 'gcis:downloadURL' in entity_doc:
            match = file_url_re.search(entity_doc['gcis:downloadURL'])
            if match:
                entity_doc['gcis:downloadURL'] = 'http://%s:8085/%s' % match.groups()
        entity_doc['identifier'] = entity_doc.get('gcis:downloadURL', k)
        entity_doc['id'] = hashlib.md5(entity_doc['identifier']).hexdigest()
        if 'prov:type' not in entity_doc:
            if 'gcis:downloadURL' in entity_doc:
                entity_doc['prov:type'] = 'eos:dataset'
            else:
                raise RuntimeError("Failed to get prov:type.")
        entity_doc['prov:concept'] = 'prov:Entity'
        entity_docs[k] = entity_doc
    
    #print(json.dumps(entity_docs, indent=2))
    
    
    # create eos:processStep doc
    act_doc = copy.deepcopy(prov_es_json['activity']['hysds:job'])
    act_doc['identifier'] = act_doc['hysds:job_id']
    act_doc['id'] = hashlib.md5(act_doc['identifier']).hexdigest()
    act_doc['prov:concept'] = "prov:Activity"
    act_doc['prov:startTime'] = act_doc['prov:startTime'].replace('+00:00', '')
    act_doc['prov:endTime'] = act_doc['prov:endTime'].replace('+00:00', '')
    act_doc['prov:used'] = []
    act_doc['prov:generated'] = []

    # save product url
    act_doc['prod_url'] = prod_url
    
    # process prov:Used
    for k in prov_es_json['used']:
        ent_key = prov_es_json['used'][k]['prov:entity']
        act_doc['prov:used'].append(entity_docs[ent_key]['identifier'])
    
    # process prov:wasGeneratedBy
    for k in prov_es_json['wasGeneratedBy']:
        ent_key = prov_es_json['wasGeneratedBy'][k]['prov:entity']
        act_doc['prov:generated'].append(entity_docs[ent_key]['identifier'])
    
    #print(json.dumps(act_doc, indent=2))

    # index processStep
    act_doc['prov_es_json'] = prov_es_json
    conn.index(act_doc, index, 'activity', act_doc['id'])
    
    # index agents
    for k in agent_docs:
        doc = agent_docs[k]
        doc['prov_es_json'] = prov_es_json
        conn.index(doc, index, 'agent', doc['id'])
        
    # index entities
    for k in entity_docs:
        doc = entity_docs[k]
        doc['prov_es_json'] = prov_es_json
        conn.index(doc, index, 'entity', doc['id'])

    print("indexed %s/prov_es.json" % prod_url)
