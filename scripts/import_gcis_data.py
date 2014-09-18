#!/usr/bin/env python
import os, json, requests
from pyes import ES

from gcis import create_app


def get_es_conn(es_url, index, settings, mapping):
    """Create connection and create index if it doesn't exist."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index, settings)
    return conn


def index_figures(gcis_url, es_url, index, settings, mapping):
    """Index GCIS figures into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings, mapping)
    conn.indices.put_mapping('figure', mapping, [index])
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


def index_findings(gcis_url, es_url, index, settings, mapping):
    """Index GCIS findings into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings, mapping)
    conn.indices.put_mapping('finding', mapping, [index])
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


def index_tables(gcis_url, es_url, index, settings, mapping):
    """Index GCIS tables into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings, mapping) 
    conn.indices.put_mapping('table', mapping, [index])
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


if __name__ == "__main__":
    env = os.environ.get('GCIS_ENV', 'prod')
    app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ELASTICSEARCH_URL']
    gcis_url =  app.config['GCIS_REST_URL']
    index = app.config['GCIS_ELASTICSEARCH_INDEX']
    with open(app.config['GCIS_ELASTICSEARCH_SETTINGS']) as f:
        settings = json.load(f)
    with open(app.config['GCIS_ELASTICSEARCH_MAPPING']) as f:
        mapping = json.load(f)


    index_figures(gcis_url, es_url, index, settings, mapping)
    index_findings(gcis_url, es_url, index, settings, mapping)
    index_tables(gcis_url, es_url, index, settings, mapping)
