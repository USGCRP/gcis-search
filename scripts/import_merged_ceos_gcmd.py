#!/usr/bin/env python
import os, json
import unicodecsv as csv
from pprint import pprint

from gcis import create_app

from import_gcis_data import get_es_conn


def import_csv(csv_file, es_url, index, settings, mapping):
    """Import CSV into elasticsearch."""

    conn = get_es_conn(es_url, index, settings, mapping)
    conn.indices.put_mapping('instrument', mapping, [index])
    with open(csv_file, 'rU') as f:
        r = csv.reader(f, encoding='windows-1252')
        for i, row in enumerate(r):
            if i == 0:
                headers = [v.lower().replace(' ', '_').replace('&', 'and') for v in row]
                continue
            print(row)
            d = dict(zip(headers, row))
            #print json.dumps(d, indent=2, sort_keys=True)
            conn.index(d, index, 'instrument', d['instrument_name_short'])


if __name__ == "__main__":
    env = os.environ.get('GCIS_ENV', 'prod')
    app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ELASTICSEARCH_URL']
    gcis_url =  app.config['GCIS_REST_URL']
    index = app.config['CEOS_GCMD_ELASTICSEARCH_INDEX']
    with open(app.config['CEOS_GCMD_ELASTICSEARCH_SETTINGS']) as f:
        settings = json.load(f)
    with open(app.config['CEOS_GCMD_ELASTICSEARCH_MAPPING']) as f:
        mapping = json.load(f)

    csv_file = os.path.join(os.path.dirname(__file__), 'data',
                            'instruments-merged_ceos_gcmd-20140912.csv')
    import_csv(csv_file, es_url, index, settings, mapping)
