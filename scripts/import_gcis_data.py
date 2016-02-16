#!/usr/bin/env python
<<<<<<< HEAD
import os, sys, json, requests, types, re, copy
from datetime import datetime
import requests_cache

from fv_prov_es import create_app
from fv_prov_es.lib.import_utils import get_es_conn, import_prov

from prov_es.model import (get_uuid, ProvEsDocument, GCIS, PROV, PROV_TYPE,
                           PROV_ROLE, PROV_LABEL, PROV_LOCATION, HYSDS)
=======
import os, json, requests, types, re
import requests_cache
from pyes import ES

from gcis import create_app
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9


requests_cache.install_cache('gcis-import')


<<<<<<< HEAD
def get_image_prov(j, gcis_url):
    """Generate PROV-ES JSON from GCIS image metadata."""

    # create doc
    doc = ProvEsDocument()
    bndl = None

    # create image, figure, chapter and report entities
    img_id = GCIS["%s" % j['uri'][1:].replace('/', '-')]
    img_title = j['title']
    img_url = None
    img_thumbnail_url = None
    for file_md in j.get('files', []):
        img_url = file_md['href']
        img_thumbnail_url = file_md['thumbnail_href']
    img_attrs = [
        ( PROV_TYPE, GCIS['Image'] ),
        ( PROV_LABEL, img_title ),
    ]
    if img_url is None:
        img_attrs.append(( PROV_LOCATION, "%s%s" % (gcis_url, j['uri']) ))
    else:
        img_attrs.append(( PROV_LOCATION, img_url ))
    if img_thumbnail_url is None:
        img_attrs.append(( HYSDS['thumbnail'], img_thumbnail_url ))
    doc.entity(img_id, img_attrs)
    reports = []
    chapters = []
    findings = []
    figures = []
    for figure in j.get('figures', []):
        report_uri = "/report/%s" % figure['report_identifier']
        chapter_uri = "/chapter/%s" % figure['chapter_identifier']
        figure_uri = "/figure/%s" % figure['identifier']

        # create report
        r = requests.get('%s%s.json' % (gcis_url, report_uri))
        r.raise_for_status()
        report = r.json()
        report_id = GCIS["%s" % report_uri[1:].replace('/', '-')]
        if report_id not in reports:
            doc.entity(report_id, [
                ( PROV_TYPE, GCIS['Report'] ),
                ( PROV_LABEL, report['title'] ),
                ( PROV_LOCATION, report['url'] ),
            ])
            reports.append(report_id)

        # create chapter
        r = requests.get('%s%s%s.json' % (gcis_url, report_uri, chapter_uri))
        if r.status_code != 200:
            print("Failed with %d code: %s" % (r.status_code, r.content))
            continue
        r.raise_for_status()
        chapter = r.json()
        chapter_id = GCIS["%s" % chapter_uri[1:].replace('/', '-')]
        if chapter_id not in chapters:
            doc.entity(chapter_id, [
                ( PROV_TYPE, GCIS['Chapter'] ),
                ( PROV_LABEL, chapter['title'] ),
                ( PROV_LOCATION, chapter['url'] ),
            ])
            chapters.append(chapter_id)
        doc.hadMember(report_id, chapter_id)
         
        # create findings
        r = requests.get('%s%s%s/finding.json' % (gcis_url, report_uri, chapter_uri))
        r.raise_for_status()
        for f in r.json():
            finding_id = GCIS["%s" % f['identifier']]
            if finding_id not in findings:
                doc.entity(finding_id, [
                    ( PROV_TYPE, GCIS['Finding'] ),
                    ( PROV_LABEL, f['identifier'] ),
                    ( PROV_LOCATION, f['href'] ),
                ])
                findings.append(finding_id)
            doc.hadMember(report_id, finding_id)
            doc.hadMember(chapter_id, finding_id)
         
        # create figure
        r = requests.get('%s%s%s%s.json' % (gcis_url, report_uri, chapter_uri, figure_uri))
        r.raise_for_status()
        figure_md = r.json()
        figure_id = GCIS["%s" % figure_uri[1:].replace('/', '-')]
        if figure_id not in figures:
            doc.entity(figure_id, [
                ( PROV_TYPE, GCIS['Figure'] ),
                ( PROV_LABEL, figure_md['title'] ),
                ( PROV_LOCATION, "%s%s" % (gcis_url, figure_md['uri']) ),
            ])
            figures.append(figure_id)
            doc.hadMember(chapter_id, figure_id)
        doc.hadMember(figure_id, img_id)

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
        if len(cont['organization']) > 0:
            org = cont['organization']
            org_id = GCIS["%s" % cont['organization']['identifier']]
            if org_id not in org_ids:          
                doc.governingOrganization(org_id, cont['organization']['name'])
                org_ids[org_id] = True
            if agent_id in agent_ids: agent_ids[agent_id].append(org_id)

    # create activity
    start_time = j['create_dt']
    end_time = j['create_dt']
    for parent in j.get('parents', []):
        input_id = GCIS["%s" % parent['url'][1:].replace('/', '-')]
        input_name = parent['label']
        doc.entity(input_id, [
            ( PROV_TYPE, GCIS["Dataset"] ),
            ( PROV_LABEL, input_name ),
            ( PROV_LOCATION, "%s%s" % (gcis_url, parent['url']) ),
        ])
        # some activity uri's are null
        if parent['activity_uri'] is None:
            act_id = GCIS["derive-from-%s" % input_id]
        else:
            act_id = GCIS["%s" % parent['activity_uri'][1:].replace('/', '-')]
        attrs = []
        for agent_id in agent_ids:
            waw_id = GCIS["%s" % get_uuid("%s:%s" % (act_id, agent_id))]
            doc.wasAssociatedWith(act_id, agent_id, None, waw_id, {'prov:role': GCIS['Contributor']})
            for org_id in agent_ids[agent_id]:
                del_id = GCIS["%s" % get_uuid("%s:%s:%s" % (agent_id, org_id, act_id))]
                doc.delegation(agent_id, org_id, act_id, del_id, {'prov:type': GCIS['worksAt']})
        for org_id in org_ids:
            waw_id = GCIS["%s" % get_uuid("%s:%s" % (act_id, org_id))]
            doc.wasAssociatedWith(act_id, org_id, None, waw_id, {'prov:role': GCIS['Funder']})
        act = doc.activity(act_id, start_time, end_time, attrs)
        doc.used(act, input_id, start_time, GCIS["%s" % get_uuid("%s:%s" % (act_id, input_id))])
        doc.wasGeneratedBy(img_id, act, end_time, GCIS["%s" % get_uuid("%s:%s" % (img_id, act_id))])
           
    # serialize
    prov_json = json.loads(doc.serialize())

    # for hadMember relations, add prov:type
    for hm_id in prov_json.get('hadMember', {}):
        hm = prov_json['hadMember'][hm_id]
        col = hm['prov:collection'] 
        ent = hm['prov:entity'] 
        if col in reports and ent in chapters:
            hm['prov:type'] = GCIS['hasChapter']
        elif col in chapters and ent in figures:
            hm['prov:type'] = GCIS['hasFigure']
        elif col in figures and ent == img_id:
            hm['prov:type'] = GCIS['hasImage']

    #print(json.dumps(prov_json, indent=2))

    return prov_json


def index_gcis(gcis_url, es_url, index, alias):
    """Index GCIS into PROV-ES ElasticSearch index."""

    conn = get_es_conn(es_url, index, alias)
    r = requests.get('%s/image.json' % gcis_url, params={ 'all': 1 })
    r.raise_for_status()
    imgs = r.json()
    #print(json.dumps(images, indent=2))
    #print(len(images))
    for img in imgs:
        img_id = img['identifier']
        img_href = img['href']
        r2 = requests.get(img_href, params={ 'all': 1 })
        r2.raise_for_status()
        img_md = r2.json()
        #print(json.dumps(img_md, indent=2))
        prov = get_image_prov(img_md, gcis_url)
        #print(json.dumps(prov, indent=2))
        import_prov(conn, index, alias, prov)


if __name__ == "__main__":
    env = os.environ.get('PROVES_ENV', 'prod')
    app = create_app('fv_prov_es.settings.%sConfig' % env.capitalize(), env=env)
    es_url = app.config['ES_URL']
    gcis_url =  "http://data.globalchange.gov"
    dt = datetime.utcnow()
    #index = "%s-%04d.%02d.%02d" % (app.config['PROVES_ES_PREFIX'],
    #                               dt.year, dt.month, dt.day)
    index = "%s-gcis" % app.config['PROVES_ES_PREFIX']
    alias = app.config['PROVES_ES_ALIAS']
    index_gcis(gcis_url, es_url, index, alias)
=======
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
>>>>>>> e5a7a1ed002df90f31bce54d8fa2493a2752caa9
