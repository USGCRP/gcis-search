import os, sys, re, json

from flask import current_app


def get_agent_node(id, doc):
    """Return d3 agent node."""

    return {
        'id': id,
        'group': 1,
        'size': 1000,
        'shape': 'triangle-down',
        'prov_type': 'agent',
        'doc': doc,
    }


def get_activity_node(id, doc):
    """Return d3 activity node."""

    return {
        'id': id,
        'group': 2,
        'size': 3000,
        'shape': 'square',
        'prov_type': 'activity',
        'doc': doc,
    }


def get_entity_node(id, doc):
    """Return d3 activity node."""

    return {
        'id': id,
        'group': 3,
        'size': 1000,
        'prov_type': 'entity',
        'doc': doc,
    }
