import os, json, requests, types
from datetime import datetime
from flask import Blueprint, render_template, flash, request, redirect, url_for, Response, current_app, jsonify
from flask.ext.login import login_user, logout_user, login_required

from fv_prov_es import cache
from fv_prov_es.forms import LoginForm
from fv_prov_es.models import User
from fv_prov_es.lib.graphviz import add_graphviz_positions
from fv_prov_es.lib.utils import get_prov_es_json, update_dict, get_expansion_map
from fv_prov_es.lib.d3_utils import get_agent_node, get_activity_node, get_entity_node

main = Blueprint('main', __name__)


D3_NODE_FUNC = {
    'agent':       get_agent_node,
    'activity':    get_activity_node,
    'entity':      get_entity_node,
}


@main.route('/')
@cache.cached(timeout=1000)
def home():
    return render_template('facetview.html',
                           title=current_app.config['TITLE'],
                           badge=current_app.config['BADGE'],
                           description=current_app.config['DESCRIPTION'],
                           lineage_nodes_max=current_app.config['LINEAGE_NODES_MAX'],
                           current_year=datetime.now().year)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # For demonstration purposes the password in stored insecurely
        user = User.query.filter_by(username=form.username.data,
                                    password=form.password.data).first()

        if user:
            login_user(user)

            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for(".home"))
        else:
            flash("Login failed.", "danger")

    return render_template("login.html", form=form)


@main.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for(".home"))


@main.route("/restricted")
@login_required
def restricted():
    return "You can only see this if you are logged in!", 200


@main.route('/fdl', methods=['GET'])
@cache.cached(timeout=1000)
def fdl():
    """Display FDL for a particular job."""

    # get id
    id = request.args.get('id', None)
    if id is None:
        return jsonify({
            'success': False,
            'message': "No id specified."
        }), 500

    return render_template('fdl.html',
                           title='PROV-ES Lineage Graph',
                           badge=current_app.config['BADGE'],
                           lineage_nodes_max=current_app.config['LINEAGE_NODES_MAX'],
                           id=id,
                           current_year=datetime.now().year)


def expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations):
    """Expand PROV-ES for activity."""

    for pred in pem.get('activity', {}):
        obj_type = pem['activity'][pred]['type']
        obj_is_source = pem['activity'][pred]['source']
        if pred in act:
            obj_ids = act[pred] if isinstance(act[pred], (types.ListType, types.TupleType)) else [act[pred]]
            for obj_id in obj_ids:
                if obj_id in pej.get(obj_type, {}):
                    obj_doc = pej[obj_type][obj_id]
                else:
                    obj_doc = get_prov_es_json(obj_id)['_source']['prov_es_json'][obj_type][obj_id]
                viz_dict['nodes'].append(D3_NODE_FUNC[obj_type](obj_id, obj_doc))
                nodes.append(obj_id)
                if obj_type == "agent": links_ref = associations
                elif obj_type == "entity": links_ref = a2e_relations
                else: links_ref = None
                if links_ref is not None:
                    if obj_is_source:
                        links_ref.append({
                            'source': obj_id,
                            'target': a,
                            'concept': pred,
                        })
                    else:
                        links_ref.append({
                            'source': a,
                            'target': obj_id,
                            'concept': pred,
                        })
        

def expand_entity_prov(e, ent, pem, pej, nodes, viz_dict, e2e_relations):
    """Expand PROV-ES for entity."""
   
    for pred in pem.get('entity', {}):
        obj_type = pem['entity'][pred]['type']
        obj_is_source = pem['entity'][pred]['source']
        if pred in ent:
            obj_ids = ent[pred] if isinstance(ent[pred], (types.ListType, types.TupleType)) else [ent[pred]]
            for obj_id in obj_ids:
                if obj_id in pej.get(obj_type, {}):
                    obj_doc = pej[obj_type][obj_id]
                else:
                    obj_doc = get_prov_es_json(obj_id)['_source']['prov_es_json'][obj_type][obj_id]
                viz_dict['nodes'].append(D3_NODE_FUNC[obj_type](obj_id, obj_doc))
                nodes.append(obj_id)
                if obj_type in ("agent", "entity"): links_ref = e2e_relations
                else: links_ref = None
                if links_ref is not None:
                    if obj_is_source:
                        links_ref.append({
                            'source': obj_id,
                            'target': e,
                            'concept': pred,
                        })
                    else:
                        links_ref.append({
                            'source': e,
                            'target': obj_id,
                            'concept': pred,
                        })
        

@cache.cached(timeout=1000)
def parse_d3(pej):
    """Return d3 node data structure for an activity, entity, or agent."""

    # get expansion map
    pem = get_expansion_map()
    current_app.logger.debug("prov_expansion_map: %s" % json.dumps(pem, indent=2))
    current_app.logger.debug("pej: %s" % json.dumps(pej, indent=2))

    # viz dict
    nodes = [] 
    input_ents = []
    output_ents = []
    associations = []
    delegations = []
    e2e_relations = []
    a2e_relations = []
    viz_dict = {'nodes': [], 'links': []}

    # add agent nodes
    for a in pej.get('agent', {}):
        viz_dict['nodes'].append(get_agent_node(a, pej['agent'][a]))
        nodes.append(a)

    # add activities
    for a in pej.get('activity', {}):
        act = pej['activity'][a]
        viz_dict['nodes'].append(get_activity_node(a, act))
        nodes.append(a)
        expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations)
        
    # add entities
    for e in pej.get('entity', {}):
        ent = pej['entity'][e]
        viz_dict['nodes'].append(get_entity_node(e, ent))
        nodes.append(e)
        expand_entity_prov(e, ent, pem, pej, nodes, viz_dict, e2e_relations)
        
    # add used links
    for u in pej.get('used', {}):
        used = pej['used'][u]

        # get activity
        a = used['prov:activity']
        if a in pej.get('activity', {}):
            act = pej['activity'][a]
        else:
            act = get_prov_es_json(a)['_source']['prov_es_json']['activity'][a]
        viz_dict['nodes'].append(get_activity_node(a, act))
        nodes.append(a)
        expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations)

        # get entity
        e = used['prov:entity']
        if e in pej.get('entity', {}):
            ent = pej['entity'][e]
        else:
            ent = get_prov_es_json(e)['_source']['prov_es_json']['entity'][e]
        viz_dict['nodes'].append(get_entity_node(e, ent))
        nodes.append(e)
        expand_entity_prov(e, ent, pem, pej, nodes, viz_dict, e2e_relations)
        
        viz_dict['links'].append({
            'source': nodes.index(a),
            'target': nodes.index(e),
            'type': 'used',
            'concept': 'prov:used',
            'value': 1,
            'doc': used,
        })
        input_ents.append(e)
        
    # add generated links
    for g in pej.get('wasGeneratedBy', {}):
        gen = pej['wasGeneratedBy'][g]

        # get activity
        a = gen['prov:activity']
        if a in pej.get('activity', {}):
            act = pej['activity'][a]
        else:
            act = get_prov_es_json(a)['_source']['prov_es_json']['activity'][a]
        viz_dict['nodes'].append(get_activity_node(a, act))
        nodes.append(a)
        expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations)
        
        # get entity
        e = gen['prov:entity']
        if e in pej.get('entity', {}):
            ent = pej['entity'][e]
        else:
            ent = get_prov_es_json(e)['_source']['prov_es_json']['entity'][e]
        viz_dict['nodes'].append(get_entity_node(e, ent))
        nodes.append(e)
        expand_entity_prov(e, ent, pem, pej, nodes, viz_dict, e2e_relations)
        
        viz_dict['links'].append({
            'source': nodes.index(e),
            'target': nodes.index(a),
            'type': 'wasGeneratedBy',
            'concept': 'prov:wasGeneratedBy',
            'value': 1,
            'doc': gen,
        })
        output_ents.append(e)
        
    # add hadMember links
    for h in pej.get('hadMember', {}):
        hm = pej['hadMember'][h]

        # get collection
        c = hm['prov:collection']
        if c in pej.get('entity', {}):
            col = pej['entity'][c]
        else:
            col = get_prov_es_json(c)['_source']['prov_es_json']['entity'][c]
            viz_dict['nodes'].append(get_entity_node(c, col))
            nodes.append(c)
        
        # get entity
        e = hm['prov:entity']
        if e in pej.get('entity', {}):
            ent = pej['entity'][e]
        else:
            ent = get_prov_es_json(e)['_source']['prov_es_json']['entity'][e]
            viz_dict['nodes'].append(get_entity_node(e, ent))
            nodes.append(e)
        
        e2e_relations.append({
            'source': c,
            'target': e,
            'concept': hm.get('prov:type', 'prov:hadMember'),
            'doc': hm,
        })
        
    # add association links
    for w in pej.get('wasAssociatedWith', {}):
        waw = pej['wasAssociatedWith'][w]

        # get activity
        a = waw['prov:activity']
        if a in pej.get('activity', {}):
            act = pej['activity'][a]
        else:
            act = get_prov_es_json(a)['_source']['prov_es_json']['activity'][a]
        viz_dict['nodes'].append(get_activity_node(a, act))
        nodes.append(a)
        expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations)
        
        # get agent
        ag = waw['prov:agent']
        if ag in pej.get('agent', {}):
            agent = pej['agent'][ag]
        else:
            agent = get_prov_es_json(ag)['_source']['prov_es_json']['agent'][ag]
        viz_dict['nodes'].append(get_agent_node(ag, agent))
        nodes.append(ag)
        #expand_agent_prov(ag, agent, pem, pej, nodes, viz_dict, associations)

        associations.append({
            'source': ag,
            'target': a,
            'doc': waw,
        })

    # add delegation links
    for d in pej.get('actedOnBehalfOf', {}):
        dlg = pej['actedOnBehalfOf'][d]

        # get activity
        a = dlg['prov:activity']
        if a in pej.get('activity', {}):
            act = pej['activity'][a]
        else:
            act = get_prov_es_json(a)['_source']['prov_es_json']['activity'][a]
        viz_dict['nodes'].append(get_activity_node(a, act))
        nodes.append(a)
        expand_activity_prov(a, act, pem, pej, nodes, viz_dict, associations, a2e_relations)
        
        # get delegate agent
        dlg_ag = dlg['prov:delegate']
        if dlg_ag in pej.get('agent', {}):
            dlg_agent = pej['agent'][dlg_ag]
        else:
            dlg_agent = get_prov_es_json(dlg_ag)['_source']['prov_es_json']['agent'][dlg_ag]
        viz_dict['nodes'].append(get_agent_node(dlg_ag, dlg_agent))
        nodes.append(dlg_ag)
        #expand_agent_prov(ag, agent, pem, pej, nodes, viz_dict, associations)

        # get responsible agent
        rsp_ag = dlg['prov:responsible']
        if rsp_ag in pej.get('agent', {}):
            rsp_agent = pej['agent'][rsp_ag]
        else:
            rsp_agent = get_prov_es_json(rsp_ag)['_source']['prov_es_json']['agent'][rsp_ag]
        viz_dict['nodes'].append(get_agent_node(rsp_ag, rsp_agent))
        nodes.append(rsp_ag)
        #expand_agent_prov(ag, agent, pem, pej, nodes, viz_dict, associations)

        delegations.append({
            'source': dlg_ag,
            'target': rsp_ag,
            'doc': dlg,
        })

    # modify color of entities that are inputs and outputs or just outputs
    new_nodes = []
    for n in viz_dict['nodes']:
        if n['id'] in input_ents and n['id'] in output_ents:
            n['group'] = 6
        elif n['id'] in output_ents:
            n['group'] = 5
        elif n['id'] in input_ents:
            n['group'] = 4
        new_nodes.append(n)
    viz_dict['nodes'] = new_nodes
    
    # add association links
    asc_dict = {}
    for a in associations:
        asc = "%s_%s" % (a['source'], a['target'])
        if asc in asc_dict: continue
        viz_dict['links'].append({
            'source': nodes.index(a['source']),
            'target': nodes.index(a['target']),
            'type': 'associated',
            'concept': 'prov:wasAssociatedWith',
            'value': 1,
            'doc': a.get('doc', None),
        })
        asc_dict[asc] = True

    # add delegation links
    dlg_dict = {}
    for d in delegations:
        dlg = "%s_%s" % (d['source'], d['target'])
        if dlg in dlg_dict: continue
        viz_dict['links'].append({
            'source': nodes.index(d['source']),
            'target': nodes.index(d['target']),
            'type': 'delegated',
            'concept': 'prov:actedOnBehalfOf',
            'value': 1,
            'doc': d.get('doc', None),
        })
        dlg_dict[dlg] = True

    # add e2e_relations links
    e2e_rel_dict = {}
    for r in e2e_relations:
        rel = "%s_%s" % (r['source'], r['target'])
        if rel in e2e_rel_dict: continue
        if r['source'] not in nodes or r['target'] not in nodes: continue
        viz_dict['links'].append({
            'source': nodes.index(r['source']),
            'target': nodes.index(r['target']),
            'type': 'e2e_related',
            'concept': r['concept'],
            'value': 1,
            'doc': r.get('doc', None),
        })
        e2e_rel_dict[rel] = True

    # add a2e_relations links
    a2e_rel_dict = {}
    for r in a2e_relations:
        rel = "%s_%s" % (r['source'], r['target'])
        if rel in a2e_rel_dict: continue
        if r['source'] not in nodes or r['target'] not in nodes: continue
        viz_dict['links'].append({
            'source': nodes.index(r['source']),
            'target': nodes.index(r['target']),
            'type': 'a2e_related',
            'concept': r['concept'],
            'value': 1,
            'doc': r.get('doc', None),
        })
        a2e_rel_dict[rel] = True

    #current_app.logger.debug("viz_dict: %s" % json.dumps(viz_dict, indent=2))
    return viz_dict
       

@main.route('/fdl/data', methods=['GET'])
@cache.cached(timeout=1000)
def fdl_data():
    """Get FDL data for visualization."""

    # get id
    id = request.args.get('id', None)
    if id is None:
        return jsonify({
            'success': False,
            'message': "No id specified."
        }), 500
    lineage = request.args.get('lineage', 'false')

    # do lineage?
    if lineage == "false":
        #current_app.logger.debug("prov_es_json: %s" % json.dumps(get_prov_es_json(id), indent=2))
        viz_dict = parse_d3(get_prov_es_json(id)['_source']['prov_es_json'])
    else:
        es_url = current_app.config['ES_URL']
        es_index = current_app.config['PROVES_ES_ALIAS']
        query = { 'query': { 'query_string': { 'query': '"%s"' % id } } }
        #current_app.logger.debug("ES query for query(): %s" % json.dumps(query, indent=2))
        r = requests.post('%s/%s/_search?search_type=scan&scroll=60m&size=100' %
                          (es_url, es_index), data=json.dumps(query))
        scan_result = r.json()
        if r.status_code != 200:
            current_app.logger.debug("Failed to query ES. Got status code %d:\n%s" %
                                     (r.status_code, json.dumps(scan_result, indent=2)))
        r.raise_for_status()

        # get results
        results = []
        scroll_id = scan_result['_scroll_id']
        while True:
            r = requests.post('%s/_search/scroll?scroll=10m' % es_url, data=scroll_id)
            res = r.json()
            scroll_id = res['_scroll_id']
            if len(res['hits']['hits']) == 0: break
            results.extend(res['hits']['hits'])

            # break at 100 results or else FDL gets overwhelmed
            if len(results) > 100: break

        #current_app.logger.debug("result: %s" % pformat(r.json()))
        current_app.logger.debug("results: %d" % len(results))
        merged_doc = {}
        for d in results:
            merged_doc = update_dict(merged_doc, d['_source']['prov_es_json'])
        #current_app.logger.debug("merged_doc: %s" % json.dumps(merged_doc, indent=2))
        viz_dict = parse_d3(merged_doc)

    #current_app.logger.debug("fdl_data viz_dict: %s" % json.dumps(viz_dict, indent=2))
    return jsonify(viz_dict)


@main.route('/fdl/data/layout', methods=['POST'])
@cache.cached(timeout=1000)
def layout():
    """Return graphviz locations for FDL data for visualization."""

    # get viz dict
    viz_dict = request.form.get('viz_dict', None)
    if viz_dict is None:
        return jsonify({
            'success': False,
            'message': "No viz_dict specified."
        }), 500
    viz_dict = json.loads(viz_dict)

    # add graphviz position
    viz_dict = add_graphviz_positions(viz_dict)

    return jsonify(viz_dict)


@main.route('/search_bundle', methods=['GET'])
@cache.cached(timeout=1000)
def search_bundle():
    """Redirect to faceted view of all docs related to a doc."""

    # get viz dict
    id = request.args.get('id', None)
    if id is None:
        return jsonify({
            'success': False,
            'message': "No id specified."
        }), 500

    # query
    query = {
        "query": {
            "query_string": {
                "query": '"%s"' % id
            }
        }
    }
    return redirect(url_for(".home", source=json.dumps(query)))
