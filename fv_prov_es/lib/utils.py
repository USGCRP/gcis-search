import os, sys, re, json, requests, collections
from StringIO import StringIO
from lxml.etree import XMLParser, parse, tostring
from tempfile import mkstemp
from subprocess import check_call

from flask import current_app

from fv_prov_es import cache


def get_etree(xml):
    """Return a tuple of [lxml etree element, prefix->namespace dict].
    """

    parser = XMLParser(remove_blank_text=True)
    if xml.startswith('<?xml') or xml.startswith('<'):
        return (parse(StringIO(xml), parser).getroot(),
                get_ns_dict(xml))
    else:
        if os.path.isfile(xml): xml_str = open(xml).read()
        else: xml_str = urlopen(xml).read()
        return (parse(StringIO(xml_str), parser).getroot(),
                get_ns_dict(xml_str))


def get_ns_dict(xml):
    """Take an xml string and return a dict of namespace prefixes to
    namespaces mapping."""
    
    nss = {} 
    def_cnt = 0
    matches = re.findall(r'\s+xmlns:?(\w*?)\s*=\s*[\'"](.*?)[\'"]', xml)
    for match in matches:
        prefix = match[0]; ns = match[1]
        if prefix == '':
            def_cnt += 1
            prefix = '_' * def_cnt
        nss[prefix] = ns
    return nss


def xpath(elt, xp, ns, default=None):
    """Run an xpath on an element and return the first result.  If no results
    were returned then return the default value."""
    
    res = elt.xpath(xp, namespaces=ns)
    if len(res) == 0: return default
    else: return res[0]
    

def pprint_xml(et):
    """Return pretty printed string of xml element."""
    
    return tostring(et, pretty_print=True)


def update_dict(d, u):
    """Recursively update dict."""

    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


@cache.cached(timeout=1000)
def get_prov_es_json(id):
    """Get PROV-ES document by ID."""

    # query
    es_url = current_app.config['ELASTICSEARCH_URL']
    es_index = current_app.config['PROVES_ELASTICSEARCH_ALIAS']
    query = { 'query': { 'term': { '_id': id } } }
    #current_app.logger.debug("ES query for query(): %s" % json.dumps(query, indent=2))
    r = requests.post('%s/%s/_search' % (es_url, es_index), data=json.dumps(query))
    result = r.json()
    if r.status_code != 200:
        current_app.logger.debug("Failed to query ES. Got status code %d:\n%s" %
                                 (r.status_code, json.dumps(result, indent=2)))
    r.raise_for_status()
    #current_app.logger.debug("result: %s" % pformat(r.json()))

    # return only result
    if len(result['hits']['hits']) > 0:
        return result['hits']['hits'][0]
    else: return {}


@cache.cached(timeout=1000)
def get_ttl(pej):

    # clean out prov:type from hadMember since provToolbox will bomb on it
    for hm_id in pej.get('hadMember', {}):
        hm = pej['hadMember'][hm_id]
        if 'prov:type' in hm: del hm['prov:type']

    # get ttl using ProvToolbox
    json_file = mkstemp(suffix='.json')[1]
    ttl_file = mkstemp(suffix='.ttl')[1]
    provconvert_cmd = os.path.normpath(
                          os.path.join(current_app.root_path, '..', 'scripts',
                                       'provToolbox', 'bin', 'provconvert')
                      )
    with open(json_file, 'w') as f:
        json.dump(pej, f, indent=2)
    #current_app.logger.debug(" ".join([provconvert_cmd, '-infile', json_file, '-outfile', ttl_file]))
    status = check_call([provconvert_cmd, '-infile', json_file, '-outfile', ttl_file])
    with open(ttl_file) as f:
        ttl = f.read()
    os.unlink(json_file)
    os.unlink(ttl_file)
    return ttl
