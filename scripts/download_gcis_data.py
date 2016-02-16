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
                         params={ 'all': 1, 'with_regions': 1 })
        r.raise_for_status()
        figures = r.json()
        fig_dir = 'figures_by_report'
        if not os.path.isdir(fig_dir):
            os.makedirs(fig_dir)
        fig_file = os.path.join(fig_dir, 'figures_%s.json' % report_id)
        with open(fig_file, 'w') as f:
            json.dump(figures, f, indent=2)


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
                         params={ 'all': 1, 'with_regions': 1 })
        r.raise_for_status()
        findings = r.json()
        fin_dir = 'findings_by_report'
        if not os.path.isdir(fin_dir):
            os.makedirs(fin_dir)
        fin_file = os.path.join(fin_dir, 'findings_%s.json' % report_id)
        with open(fin_file, 'w') as f:
            json.dump(findings, f, indent=2)


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
                         params={ 'all': 1, 'with_regions': 1 })
        r.raise_for_status()
        tables = r.json()
        tab_dir = 'tables_by_report'
        if not os.path.isdir(tab_dir):
            os.makedirs(tab_dir)
        tab_file = os.path.join(tab_dir, 'tables_%s.json' % report_id)
        with open(tab_file, 'w') as f:
            json.dump(tables, f, indent=2)


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
