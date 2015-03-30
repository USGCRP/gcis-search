import os, sys, json
from tempfile import mkstemp
from pydot import Dot, Subgraph, Node, Edge

from flask import current_app
from .utils import get_etree


def get_session_svg(viz_data):
    """Take session visualization data and return svg."""
    
    graph = Dot('graphname', graph_type='digraph')
    
    #loop create all nodes and store by id
    node_dict = {}
    for i, node_data in enumerate(viz_data['nodes']):
        id = node_data['id']
        node_dict[id] = str(i)
        graph.add_node(Node(str(i)))
        
    #add edges by links
    for link_data in viz_data['links']:
        snode = node_dict[viz_data['nodes'][link_data['source']]['id']]
        tnode = node_dict[viz_data['nodes'][link_data['target']]['id']]
        graph.add_edge(Edge(snode, tnode))
    
    #get svg of graph
    tmp, file = mkstemp()
    graph.write_svg(file)
    svg = open(file).read()
    os.unlink(file)
    
    #f = open('/tmp/session/session.svg', 'w')
    #f.write("%s\n" % svg)
    #f.close()

    return svg

def add_graphviz_positions(viz_data):
    """Take viz data and add positions as determined by graphviz."""
    
    #get svg
    svg = get_session_svg(viz_data)
    
    #parse svg
    #get xml etree
    et, nsdict = get_etree(svg)
    #log.debug(nsdict)
    
    #loop over each node and set x and y positions
    min_y = 0
    for i, node_data in enumerate(viz_data['nodes']):
        id = node_data['id']
        el_elt = et.xpath('.//_:g/_:ellipse[../_:title = "%s"]' % str(i), namespaces=nsdict)
        if len(el_elt) != 1: raise RuntimeError("Failed to xpath query node %s." % str(i))
        else: el_elt = el_elt[0]
        node_data['gv_x'] = int(eval(el_elt.get('cx')))
        node_data['gv_y'] = int(eval(el_elt.get('cy')))
        if node_data['gv_y'] < min_y: min_y = node_data['gv_y']
        
    #move y values into the positive
    for node_data in viz_data['nodes']: node_data['gv_y'] -= min_y
        
    return viz_data
