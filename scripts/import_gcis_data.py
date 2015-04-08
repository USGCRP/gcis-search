#!/usr/bin/env python
import os, sys, json, requests, types, re, copy
from datetime import datetime
import requests_cache

from fv_prov_es import create_app
from fv_prov_es.lib.import_utils import get_es_conn, import_prov

from prov_es.model import get_uuid, ProvEsDocument


requests_cache.install_cache('gcis-import')


def get_image_prov(j, gcis_url):
    """Generate PROV-ES JSON from GCIS image metadata."""

    # create doc
    gcis_ns = "http://data.globalchange.gov/gcis.owl#"
    doc = ProvEsDocument(namespaces={ "gcis": gcis_ns })
    bndl = None

    # create image, figure, chapter and report entities
    img_id = "gcis:%s" % j['uri'][1:].replace('/', '-')
    img_title = j['title']
    img_url = None
    img_thumbnail_url = None
    for file_md in j.get('files', []):
        img_url = file_md['href']
        img_thumbnail_url = file_md['thumbnail_href']
    img_attrs = [
        ( "prov:type", 'gcis:Image' ),
        ( "prov:label", img_title ),
    ]
    if img_url is None:
        img_attrs.append(( "prov:location", "%s%s" % (gcis_url, j['uri']) ))
    else:
        img_attrs.append(( "prov:location", img_url ))
    if img_thumbnail_url is None:
        img_attrs.append(( "hysds:thumbnail", img_thumbnail_url ))
    doc.entity(img_id, img_attrs)
    reports = []
    chapters = []
    figures = []
    for figure in j.get('figures', []):
        report_uri = "/report/%s" % figure['report_identifier']
        chapter_uri = "/chapter/%s" % figure['chapter_identifier']
        figure_uri = "/figure/%s" % figure['identifier']

        # create report
        r = requests.get('%s%s.json' % (gcis_url, report_uri))
        r.raise_for_status()
        report = r.json()
        report_id = "gcis:%s" % report_uri[1:].replace('/', '-')
        if report_id not in reports:
            doc.entity(report_id, [
                ( "prov:type", 'gcis:Report' ),
                ( "prov:label", report['title'] ),
                ( "prov:location", report['url'] ),
            ])
            reports.append(report_id)

        # create chapter
        r = requests.get('%s%s%s.json' % (gcis_url, report_uri, chapter_uri))
        r.raise_for_status()
        chapter = r.json()
        chapter_id = "gcis:%s" % chapter_uri[1:].replace('/', '-')
        if chapter_id not in chapters:
            doc.entity(chapter_id, [
                ( "prov:type", 'gcis:Chapter' ),
                ( "prov:label", chapter['title'] ),
                ( "prov:location", chapter['url'] ),
            ])
            chapters.append(chapter_id)
        doc.hadMember(report_id, chapter_id)
         
        # create figure
        r = requests.get('%s%s%s%s.json' % (gcis_url, report_uri, chapter_uri, figure_uri))
        r.raise_for_status()
        figure_md = r.json()
        figure_id = "gcis:%s" % figure_uri[1:].replace('/', '-')
        if figure_id not in figures:
            doc.entity(figure_id, [
                ( "prov:type", 'gcis:Figure' ),
                ( "prov:label", figure_md['title'] ),
                ( "prov:location", "%s%s" % (gcis_url, figure_md['uri']) ),
            ])
            figures.append(figure_id)
            doc.hadMember(chapter_id, figure_id)
        doc.hadMember(figure_id, img_id)

    # create agents
    agent_ids = []
    for cont in j.get('contributors', []):
        # replace slashes because we get prov.model.ProvExceptionInvalidQualifiedName errors
        agent_id = "gcis:%s" % cont['uri'][1:].replace('/', '-')
        agent_name  = " ".join([cont['person'][i] for i in
                               ('first_name', 'middle_name', 'last_name')
                               if cont['person'].get(i, None) is not None])
        doc.agent(agent_id, [
            ( "prov:type", "gcis:Person" ),
            ( "prov:label", agent_name ),
            ( "prov:location", "%s%s" % (gcis_url, cont['uri']) ),
        ])
        agent_ids.append(agent_id)

    # create activity
    start_time = j['create_dt']
    end_time = j['create_dt']
    for parent in j.get('parents', []):
        input_id = "gcis:%s" % parent['url'][1:].replace('/', '-')
        input_name = parent['label']
        doc.entity(input_id, [
            #( "prov:type", "gcis:Dataset" ),
            ( "prov:type", "eos:dataset", ),
            ( "prov:label", input_name ),
            ( "prov:location", "%s%s" % (gcis_url, parent['url']) ),
        ])
        # some activity uri's are null
        if parent['activity_uri'] is None:
            act_id = "gcis:derive-from-%s" % input_id
        else:
            act_id = "gcis:%s" % parent['activity_uri'][1:].replace('/', '-')
        attrs = []
        if len(agent_ids) > 0:
            attrs.append(( "prov:wasAssociatedWith", agent_ids[0] ))
        act = doc.activity(act_id, start_time, end_time, attrs)
        doc.used(act, input_id, start_time, "gcis:%s" % get_uuid("%s:%s" % (act_id, input_id)))
        doc.wasGeneratedBy(img_id, act, end_time, "gcis:%s" % get_uuid("%s:%s" % (img_id, act_id)))
           
    # serialize
    prov_json = json.loads(doc.serialize())

    # for hadMember relations, add prov:type
    for hm_id in prov_json.get('hadMember', {}):
        hm = prov_json['hadMember'][hm_id]
        col = hm['prov:collection'] 
        ent = hm['prov:entity'] 
        if col in reports and ent in chapters:
            hm['prov:type'] = 'gcis:hasChapter'
        elif col in chapters and ent in figures:
            hm['prov:type'] = 'gcis:hasFigure'
        elif col in figures and ent == img_id:
            hm['prov:type'] = 'gcis:hasImage'

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
