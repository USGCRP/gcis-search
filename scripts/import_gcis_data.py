#!/usr/bin/env python
import os, sys, json, requests, types, re, copy
from datetime import datetime
import requests_cache

from fv_prov_es import create_app
from fv_prov_es.lib.import_utils import get_es_conn, import_prov

from prov_es.model import (get_uuid, ProvEsDocument, GCIS, PROV, PROV_TYPE,
                           PROV_ROLE, PROV_LABEL, PROV_LOCATION, HYSDS)


requests_cache.install_cache('gcis-import')


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
        r = requests.get('%s%s.json' % (gcis_url, report_uri), verify=False)
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
        r = requests.get('%s%s%s.json' % (gcis_url, report_uri, chapter_uri), verify=False)
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
        r = requests.get('%s%s%s/finding.json' % (gcis_url, report_uri, chapter_uri), verify=False)
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
        r = requests.get('%s%s%s%s.json' % (gcis_url, report_uri, chapter_uri, figure_uri), verify=False)
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
    r = requests.get('%s/image.json' % gcis_url, params={ 'all': 1 }, verify=False)
    r.raise_for_status()
    imgs = r.json()
    #print(json.dumps(images, indent=2))
    #print(len(images))
    for img in imgs:
        img_id = img['identifier']
        #if img_id != 'f27374a2-d4ef-479c-8f96-9de23fedfc3e': continue
        img_href = img['href']
        r2 = requests.get(img_href, params={ 'all': '1' }, verify=False)
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
    #gcis_url =  "http://data.globalchange.gov"
    gcis_url =  "https://gcis-search-stage.jpl.net:3000"
    dt = datetime.utcnow()
    #index = "%s-%04d.%02d.%02d" % (app.config['PROVES_ES_PREFIX'],
    #                               dt.year, dt.month, dt.day)
    index = "%s-gcis" % app.config['PROVES_ES_PREFIX']
    alias = app.config['PROVES_ES_ALIAS']
    index_gcis(gcis_url, es_url, index, alias)
