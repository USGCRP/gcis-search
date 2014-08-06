#!/usr/bin/env python
import os, json, requests
from pyes import ES

from gcis import create_app


def get_es_conn(es_url, index, settings):
    """Create connection and create index if it doesn't exist."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index, settings)
    return conn


def index_figures(gcis_url, es_url, index, settings):
    """Index GCIS figures into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings) 
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
            conn.index(figure, index, 'figure', figure['identifier'])


def index_findings(gcis_url, es_url, index, settings):
    """Index GCIS findings into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings) 
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
            conn.index(finding, index, 'finding', finding['identifier'])


def index_tables(gcis_url, es_url, index, settings):
    """Index GCIS tables into ElasticSearch."""

    conn = get_es_conn(es_url, index, settings) 
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
            conn.index(table, index, 'table', table['identifier'])


if __name__ == "__main__":
    env = os.environ.get('GCIS_ENV', 'prod')
    app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ELASTICSEARCH_URL']
    gcis_url =  app.config['GCIS_REST_URL']
    index = app.config['ELASTICSEARCH_INDEX']
    with open(app.config['ELASTICSEARCH_SETTINGS']) as f:
        settings = json.load(f)

    index_figures(gcis_url, es_url, index, settings)
    index_findings(gcis_url, es_url, index, settings)
    index_tables(gcis_url, es_url, index, settings)
