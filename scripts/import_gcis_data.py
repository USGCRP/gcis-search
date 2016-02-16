#!/usr/bin/env python
import os, json, requests, types, re
import requests_cache
from pyes import ES

from gcis import create_app


requests_cache.install_cache('gcis-import')


FIGURES_RE = re.compile(r'\(figure(?:s)?\s+(\d+\.\d+)(?:\s+and\s+(\d+.\d+))?', re.I)
TABLES_RE = re.compile(r'\(table(?:s)?\s+(\d+\.\d+)(?:\s+and\s+(\d+.\d+))?', re.I)


def get_es_conn(es_url, index):
    """Create connection and create index if it doesn't exist."""

    conn = ES(es_url)
    if not conn.indices.exists_index(index):
        conn.indices.create_index(index)
    return conn


def index_reports(gcis_url, es_url, index):
    """Index GCIS reports into ElasticSearch."""

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report['report_id'] = report['identifier']
        report['report_title'] = report['title']
        conn.index(report, index, 'report', report['identifier'])


def index_chapters(gcis_url, es_url, index):
    """Index GCIS chapters into ElasticSearch."""

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report_id = report['identifier']
        r = requests.get("%s/report/%s/chapter.json" % (gcis_url, report_id),
                         params={ 'all': 1 })
        if r.status_code != 200:
            print("Skipped %s/report/%s/chapter.json: %s" % (gcis_url, report_id, r.text))
            continue
        r.raise_for_status()
        chapters = r.json()
        for chapter in chapters:
            chapter['chapter'] = { 'number': chapter['number'] }
            if 'href' in chapter:
                r = requests.get(chapter['href'])
                r.raise_for_status()
                chapter['href_metadata'] = r.json()
            chapter['report_identifier'] = chapter['href_metadata']['report_identifier']
            conn.index(chapter, index, 'chapter', chapter['identifier'])


def index_figures(gcis_url, es_url, index):
    """Index GCIS figures into ElasticSearch."""

    # cache dicts
    person_cache = {}

    conn = get_es_conn(es_url, index)
    r = requests.get("%s/report.json" % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    reports = r.json()
    for report in reports:
        report_id = report['identifier']
        r = requests.get("%s/report/%s/figure.json" % (gcis_url, report_id),
                         params={ 'all': 1 })
        if r.status_code != 200:
            print("Skipped %s/report/%s/figure.json: %s" % (gcis_url, report_id, r.text))
            continue
        r.raise_for_status()
        figures = r.json()
        for figure in figures:
            #print json.dumps(figure, indent=2)
            contributor_full_names = []
            if 'href' in figure:
                r = requests.get(figure['href'])
                r.raise_for_status()
                figure['href_metadata'] = r.json()

                # index contributors
                if 'contributors' in figure['href_metadata']:
                    for person in figure['href_metadata']['contributors']:
                        person_id = person['person_id']
                        if 'person_uri' in person and isinstance(person['person_uri'], types.StringTypes):
                            if person_id in person_cache:
                                person_info = person_cache[person_id]
                            else:
                                r = requests.get("%s%s.json" % (gcis_url, person['person_uri']))
                                r.raise_for_status()
                                person_info = r.json()
                                person_cache[person_id] = person_info
                            person_info['contributor_full_name'] = "%s %s" % (person_info['first_name'], person_info['last_name'])
                            person_info['identifier'] = person_info['contributor_full_name']
                            contributor_full_names.append(person_info['contributor_full_name'])
                            conn.index(person_info, index, 'person', person_id)

                # index chapter
                if 'chapter' in figure['href_metadata']:
                    figure['chapter'] = figure['href_metadata']['chapter']
                    if 'ordinal' in figure:
                        figure['ordinal_abs'] = "%s.%s" % (figure['chapter']['number'], figure['ordinal'])

                # index images
                if 'images' in figure['href_metadata']:
                    for image in figure['href_metadata']['images']:
                        image_id = image['identifier']
                        r = requests.get("%s/image/%s.json" % (gcis_url, image_id),
                                         params={ 'all': 1 })
                        r.raise_for_status()
                        image_info = r.json()
 
                        # index contributors
                        image_contributor_full_names = []
                        if 'contributors' in image_info:
                            for person in image_info['contributors']:
                                person_id = person['person_id']
                                if 'person_uri' in person and isinstance(person['person_uri'], types.StringTypes):
                                    if person_id in person_cache:
                                        person_info = person_cache[person_id]
                                    else:
                                        r = requests.get("%s%s.json" % (gcis_url, person['person_uri']))
                                        r.raise_for_status()
                                        person_info = r.json()
                                        person_cache[person_id] = person_info
                                    contributor_full_name = "%s %s" % (person_info['first_name'], person_info['last_name'])
                                    image_contributor_full_names.append(contributor_full_name)
                        image_info['contributor_full_name'] = image_contributor_full_names

                        # split attributes
                        if 'attributes' in image_info and isinstance(image_info['attributes'], types.StringTypes):
                            image_info['attributes'] = [ i.strip() for i in image_info['attributes'].split(',')]
 
                        conn.index(image_info, index, 'image', image_id)
   
            # add linking metadata
            figure['report_id'] = report_id
            figure['report_title'] = report['title']
            figure['contributor_full_name'] = contributor_full_names

            # split attributes
            if 'attributes' in figure and isinstance(figure['attributes'], types.StringTypes):
                figure['attributes'] = [ i.strip() for i in figure['attributes'].split(',')]
 
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
        if r.status_code != 200:
            print("Skipped %s/report/%s/figure.json: %s" % (gcis_url, report_id, r.text))
            continue
        r.raise_for_status()
        findings = r.json()
        for finding in findings:
            #print json.dumps(finding, indent=2)
            if 'href' in finding:
                r = requests.get(finding['href'])
                r.raise_for_status()
                finding['href_metadata'] = r.json()
            finding['report_id'] = report_id
            finding['report_title'] = report['title']

            # split attributes
            if 'attributes' in finding and isinstance(finding['attributes'], types.StringTypes):
                finding['attributes'] = [ i.strip() for i in finding['attributes'].split(',')]
 
            # index chapter
            if 'chapter' in finding['href_metadata']:
                finding['chapter'] = finding['href_metadata']['chapter']
                if 'ordinal' in finding:
                    finding['ordinal_abs'] = "%s.%s" % (finding['chapter']['number'], finding['ordinal'])

            # try to scrape for mention of figures and tables from evidence
            if 'evidence' in finding and finding['evidence'] is not None:

                # scrape figures
                matches = FIGURES_RE.findall(finding['evidence'])
                finding['lineage_figures'] = []
                for match1, match2 in matches:
                    #print("Got matches: %s %s" % (match1, match2))
                    finding['lineage_figures'].append(match1)
                    if match2 is not None and match2 != "":
                        finding['lineage_figures'].append(match2)

                # scrape tables
                matches = TABLES_RE.findall(finding['evidence'])
                finding['lineage_tables'] = []
                for match1, match2 in matches:
                    #print("Got matches: %s %s" % (match1, match2))
                    finding['lineage_tables'].append(match1)
                    if match2 is not None and match2 != "":
                        finding['lineage_tables'].append(match2)

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
        if r.status_code != 200:
            print("Skipped %s/report/%s/figure.json: %s" % (gcis_url, report_id, r.text))
            continue
        r.raise_for_status()
        tables = r.json()
        for table in tables:
            #print json.dumps(table, indent=2)
            if 'href' in table:
                r = requests.get(table['href'])
                r.raise_for_status()
                table['href_metadata'] = r.json()
            table['report_id'] = report_id
            table['report_title'] = report['title']

            # index chapter
            if 'chapter' in table['href_metadata']:
                table['chapter'] = table['href_metadata']['chapter']
                if 'ordinal' in table:
                    table['ordinal_abs'] = "%s.%s" % (table['chapter']['number'], table['ordinal'])

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

        # add files
        if 'files' in md:
            md.setdefault('href_metadata', {})['files'] = md['files']

        # add GeoJSON if defined (for now only bbox)
        lat_min = md.get('lat_min', None)
        lat_max = md.get('lat_max', None)
        lon_min = md.get('lon_min', None)
        lon_max = md.get('lon_max', None)
        if lat_min is not None and lat_max is not None and \
           lon_min is not None and lon_max is not None:
            lat_min = float(lat_min)
            lat_max = float(lat_max)
            lon_min = float(lon_min)
            lon_max = float(lon_max)
            if lon_min == 0. and lon_max == 360.:
                lon_min = -180.
                lon_max = 180.
            if lon_min == -180.: lon_min = -179.9
            elif lon_min > 180.: lon_min -= 360.
            if lon_max == 180.: lon_max = 179.9
            elif lon_max > 180.: lon_max -= 360.
            if lat_min == -90.: lat_min = -89.9
            if lat_max == 90.: lat_max = 89.9
            md['facetview_location'] = {
                "type": "polygon",
                "coordinates": [[
                    [ lon_min, lat_min ],
                    [ lon_min, lat_max ],
                    [ lon_max, lat_max ],
                    [ lon_max, lat_min ],
                    [ lon_min, lat_min ]
                ]]
            }

        # split attributes
        if 'attributes' in md and isinstance(md['attributes'], types.StringTypes):
            md['attributes'] = [ i.strip() for i in md['attributes'].split(',')]
 
        try: conn.index(md, index, gcis_type, md['identifier'])
        except Exception, e:
            print("Got error: %s" % str(e))
            with open('errors/%s.json' % md['identifier'], 'w') as f:
                json.dump(md, f, indent=2)
            continue


if __name__ == "__main__":
    env = os.environ.get('GCIS_ENV', 'prod')
    app = create_app('gcis.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ELASTICSEARCH_URL']
    gcis_url =  app.config['GCIS_REST_URL']
    index = app.config['GCIS_ELASTICSEARCH_INDEX']

    index_reports(gcis_url, es_url, index)
    index_chapters(gcis_url, es_url, index)
    index_figures(gcis_url, es_url, index)
    index_findings(gcis_url, es_url, index)
    index_tables(gcis_url, es_url, index)
    platforms_by_instr = index_platforms(gcis_url, es_url, index)
    index_instruments(gcis_url, es_url, index, platforms_by_instr)
    index_datasets(gcis_url, es_url, index)
