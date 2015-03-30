#!/usr/bin/env python
import os, sys, json, requests, copy, hashlib, re, csv
from datetime import datetime
from pyes import ES

from fv_prov_es import create_app


EMPTY = re.compile(r'^\s*$')


def parse_csv(file):
    """Return CSV data as JSON."""

    instrs = []
    fields = []
    with open('instruments-merged_ceos_gcmd-20140912.csv', 'rU') as f:
        r = csv.reader(f)
        for i, row in enumerate(r):
            if i == 0:
                fields = row
                continue
            info = dict(zip(fields, [s.decode('windows-1252') for s in row]))
            #print(info)
            #print(json.dumps(info, indent=2))
            instrs.append(info)
    return instrs


def import_instruments(instrs, es_url, index):
    """Create JSON ES docs and import."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index)

    # track agencies/organizations
    orgs = {}

    for instr in instrs:
        identifier = "eos:%s" % instr['Instrument Name Short']
        id = hashlib.md5(identifier).hexdigest()
        if 'Instrument Technology' in instr and not EMPTY.search(instr['Instrument Technology']):
            sensor = "eos:%s" % instr['Instrument Technology']
        else:
            if 'Instrument Type' in instr and not EMPTY.search(instr['Instrument Type']):
                sensor = "eos:%s" % instr['Instrument Type']
            else:
                if 'Subtype' in instr and not EMPTY.search(instr['Subtype']):
                    sensor = "eos:%s" % instr['Subtype']
                else:
                    if 'Type' in instr and not EMPTY.search(instr['Type']):
                        sensor = "eos:%s" % instr['Type']
                    else:
                        if 'Class' in instr and not EMPTY.search(instr['Class']):
                            sensor = "eos:%s" % instr['Class']
                        else:
                            sensor = None
        #print(instr['Instrument Technology'], sensor)
        platform = None
        if 'Instrument Agencies' in instr and not EMPTY.search(instr['Instrument Agencies']):
            org = "eos:%s" % instr['Instrument Agencies']
            if org not in orgs:
               orgs[org] = {
                   "identifier": org,
                   "prov:type": "prov:Organization",
                   "id": hashlib.md5(org).hexdigest(),
                   "prov:concept": "prov:Organization",
               }
               conn.index(orgs[org], index, 'agent', orgs[org]['id'])
        else: org = None
        doc = {
            "gcis:hasSensor": sensor,
            "gcis:inPlatform": platform,
            "prov:concept": "prov:Entity",
            "prov:type": "eos:instrument",
            "gcis:hasGoverningOrganization": org,
            "identifier": identifier,
            "id": id,
        }
        conn.index(doc, index, 'entity', doc['id'])


if __name__ == "__main__":
    env = os.environ.get('PROVES_ENV', 'prod')
    app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
    j = parse_csv('instruments-merged_ceos_gcmd-20140912.csv')
    dt = datetime.utcnow()
    index = "%s-%04d.%02d.%02d" % (app.config['PROVES_ES_PREFIX'],
                                   dt.year, dt.month, dt.day) 
    #print(json.dumps(j, indent=2, sort_keys=True))
    import_instruments(j, app.config['ES_URL'], index)
