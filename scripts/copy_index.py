#!/usr/bin/env python
import os, sys, json, requests
from pyes import ES

from fv_prov_es import create_app


# get settings
env = os.environ.get('PROVES_ENV', 'prod')
app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
es_url = app.config['ES_URL']

# get source and destination index
src = sys.argv[1]
dest = sys.argv[2]

# get connection and create destination index
conn = ES(es_url)
if not conn.indices.exists_index(dest):
    conn.indices.create_index(dest)

# index all docs from source index to destination index
query = {
  "fields": "_source",
  "query": {
    "match_all": {}
  }
}
r = requests.post('%s/%s/_search?search_type=scan&scroll=60m&size=100' % (es_url, src), data=json.dumps(query))
scan_result = r.json()
count = scan_result['hits']['total']
scroll_id = scan_result['_scroll_id']
results = []
while True:
    r = requests.post('%s/_search/scroll?scroll=60m' % es_url, data=scroll_id)
    res = r.json()
    scroll_id = res['_scroll_id']
    if len(res['hits']['hits']) == 0: break
    for hit in res['hits']['hits']:
        doc = hit['_source']
        conn.index(hit['_source'], dest, hit['_type'], hit['_id'])
        print "indexed %s" % hit['_id']
