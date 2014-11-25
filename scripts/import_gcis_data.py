#!/usr/bin/env python
import os, json, requests
from pyes import ES

from gcis import create_app


def get_es_conn(es_url, index):
    """Create connection and create index if it doesn't exist."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index)
    return conn


def index_figures(gcis_url, es_url, index):
    """Index GCIS figures into ElasticSearch."""

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report_id = report['identifier']
        r = requests.get("%s/report/%s/figure.json" % (gcis_url, report_id),
                         params={ 'all': 1 })
        r.raise_for_status()
        figures = r.json()
        for figure in figures:
            #print json.dumps(figure, indent=2)
            if 'href' in figure:
                r = requests.get(figure['href'])
                r.raise_for_status()
                figure['href_metadata'] = r.json()
            conn.index(figure, index, 'figure', figure['identifier'])


def index_findings(gcis_url, es_url, index):
    """Index GCIS findings into ElasticSearch."""

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report_id = report['identifier']
        r = requests.get("%s/report/%s/finding.json" % (gcis_url, report_id),
                         params={ 'all': 1 })
        r.raise_for_status()
        findings = r.json()
        for finding in findings:
            #print json.dumps(finding, indent=2)
            if 'href' in finding:
                r = requests.get(finding['href'])
                r.raise_for_status()
                finding['href_metadata'] = r.json()
            conn.index(finding, index, 'finding', finding['identifier'])


def index_tables(gcis_url, es_url, index):
    """Index GCIS tables into ElasticSearch."""

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report_id = report['identifier']
        r = requests.get("%s/report/%s/table.json" % (gcis_url, report_id),
                         params={ 'all': 1 })
        r.raise_for_status()
        tables = r.json()
        for table in tables:
            #print json.dumps(table, indent=2)
            if 'href' in table:
                r = requests.get(table['href'])
                r.raise_for_status()
                table['href_metadata'] = r.json()
            conn.index(table, index, 'table', table['identifier'])


def index_platforms(gcis_url, es_url, index):
    """Index GCIS platforms into ElasticSearch."""

    gcis_type = 'platform'
    conn = get_es_conn(es_url, index)
    r = requests.get("%s/%s.json" % (gcis_url, gcis_type))
    r.raise_for_status()
    results = r.json()
    platforms_by_instr = {}
    for res in results:
        res_id = res['identifier']
        r = requests.get("%s/%s/%s.json" % (gcis_url, gcis_type, res_id))
        r.raise_for_status()
        md = r.json()
        if 'files' in md:
            md.setdefault('href_metadata', {})['files'] = md['files']
        r = requests.get("%s/%s/%s/instrument.json" % (gcis_url, gcis_type, res_id))
        r.raise_for_status()
        pairs = r.json()
        instruments = []
        instr_ids = []
        for pair in pairs:
            instr_id = pair['instrument_identifier']
            r = requests.get("%s/%s/%s.json" % (gcis_url, 'instrument', instr_id))
            r.raise_for_status()
            instr_name = r.json()['name']
            instr_ids.append(instr_id)
            instruments.append(instr_name)
            platforms_by_instr.setdefault('by_name', {}).setdefault(instr_name, set()).add(md['name'])
            platforms_by_instr.setdefault('by_id', {}).setdefault(instr_id, set()).add(res_id)
        md['instrument_names'] = instruments
        md['instrument_identifiers'] = instr_ids
        md['platform_names'] = [md['name']]
        md['platform_identifiers'] = [res_id]
        conn.index(md, index, gcis_type, md['identifier'])
    return platforms_by_instr


def index_instruments(gcis_url, es_url, index, platforms_by_instr):
    """Index GCIS instruments into ElasticSearch."""

    gcis_type = 'instrument'
    conn = get_es_conn(es_url, index)
    r = requests.get("%s/%s.json" % (gcis_url, gcis_type))
    r.raise_for_status()
    results = r.json()
    for res in results:
        res_id = res['identifier']
        r = requests.get("%s/%s/%s.json" % (gcis_url, gcis_type, res_id))
        r.raise_for_status()
        md = r.json()
        if 'files' in md:
            md.setdefault('href_metadata', {})['files'] = md['files']
        md['platform_identifiers'] = platforms_by_instr['by_id'].get(res_id, [])
        md['platform_names'] = platforms_by_instr['by_name'].get(md['name'], [])
        md['instrument_names'] = [md['name']]
        md['instrument_identifiers'] = [res_id]
        conn.index(md, index, gcis_type, md['identifier'])


def index_datasets(gcis_url, es_url, index):
    """Index GCIS datasets into ElasticSearch."""

    gcis_type = 'dataset'
    conn = get_es_conn(es_url, index)
    r = requests.get("%s/%s.json" % (gcis_url, gcis_type))
    r.raise_for_status()
    results = r.json()
    for res in results:
        res_id = res['identifier']
        r = requests.get("%s/%s/%s.json" % (gcis_url, gcis_type, res_id))
        r.raise_for_status()
        md = r.json()
        if 'files' in md:
            md.setdefault('href_metadata', {})['files'] = md['files']
        conn.index(md, index, gcis_type, md['identifier'])


if __name__ == "__main__":
    env = os.environ.get('GCIS_ENV', 'prod')
    app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ELASTICSEARCH_URL']
    gcis_url =  app.config['GCIS_REST_URL']
    index = app.config['GCIS_ELASTICSEARCH_INDEX']

    index_figures(gcis_url, es_url, index)
    index_findings(gcis_url, es_url, index)
    index_tables(gcis_url, es_url, index)
    platforms_by_instr = index_platforms(gcis_url, es_url, index)
    index_instruments(gcis_url, es_url, index, platforms_by_instr)
    index_datasets(gcis_url, es_url, index)
