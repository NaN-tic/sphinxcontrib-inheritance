# -*- coding: utf-8 -*-
"""
    inheritance
    -----------

    :copyright: Copyright 2011 by NaN Projectes de Programari Lliure, S.L.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.transforms import Transform

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.compat import Directive
from docutils.parsers.rst import directives, states
from docutils import nodes

import os
import re
import tempfile


src_chars = """àáäâÀÁÄÂèéëêÈÉËÊìíïîÌÍÏÎòóöôÒÓÖÔùúüûÙÚÜÛçñºª·¤ '"()/*-+?!&$[]{}@#`'^:;<>=~%\\""" 
src_chars = unicode(src_chars, 'utf-8')
dst_chars = """aaaaAAAAeeeeEEEEiiiiIIIIooooOOOOuuuuUUUUcnoa_e______________________________"""
dst_chars = unicode(dst_chars, 'utf-8')

def unaccent(text):
    if isinstance( text, str ):
        text = unicode( text, 'utf-8' )
    output = text
    for c in xrange(len(src_chars)):
        output = output.replace( src_chars[c], dst_chars[c] )
    return output.strip('_').encode( 'utf-8' )

existing_ids = set()

#def create_id(module, value):
# TODO: Consider module?
def create_id(value):
    found = False
    word_count = 7
    while True:
        words = unaccent(value.strip()).lower()
        words = words.replace(':','_')
        words = words.replace('.','_')
        words = words.replace('_',' ')
        words = words.split()
        identifier = '_'.join(words[:word_count])

        if not identifier in existing_ids:
            found = True
            break
        word_count += 1
        if word_count > len(words):
            break

    if not found:
        counter = 1
        while True:
            new_identifier = identifier + '_%d' % counter
            if not new_identifier in existing_ids:
                identifier = new_identifier
                break
            counter += 1

    existing_ids.add(identifier)
    return identifier



def check_module(app, docname, text):
    modules = app.config.inheritance_modules
    if isinstance(modules, (str, unicode)):
        modules = [x.strip() for x in modules.split(',')]
    path = os.path.split(docname)
    if len(path) == 1:
        return
    module = path[-2]
    if not module:
        return
    if module not in modules:
        # If the module is not in the list of installed 
        # modules set as if the document was empty.
        text[0] = ''

inherits = {}


class Replacer(Transform):

    default_priority = 1000

    def apply(self):
        config = self.document.settings.env.config
        pattern = config.inheritance_pattern
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        current_inherit_ref = None
        for node in self.document.traverse():
            parent = node.parent
            text = node.astext()
            match = pattern.search(text)
            if match:
                # catch invalid pattern with too many groups
                if len(match.groups()) != 1:
                    raise ValueError(
                        'inherit_issue_pattern must have '
                        'exactly one group: {0!r}'.format(match.groups()))

                # extract the reference data (excluding the leading dash)
                refdata = match.group(1)

                id, position, ref = refdata.split(':')
                current_inherit_ref = ref
                inherits[ref] = {
                    'position': position,
                    'nodes': [],
                    }
                if parent:
                    parent.replace(node, [])
                continue

            if current_inherit_ref:
                if parent and parent in inherits[current_inherit_ref]['nodes']:
                    continue
                inherits[current_inherit_ref]['nodes'].append(node)

def init_transformer(app):
    if app.config.inheritance_plaintext:
        app.add_transform(Replacer)

def add_references(app, doctree, fromdocname):
    counter = 0
    for node in doctree.traverse():
        if isinstance(node, nodes.Inline):
            # We do not want to consider inline nodes such as emphasis, 
            # strong or literal
            continue
        
        counter += 1
        targetid = create_id(node.astext())
        targetnode = nodes.target('', '', ids=[targetid])
 
        parent = node.parent
        if not parent:
            continue
        parent.replace(node, [targetnode, node])

def replace_inheritances(app, doctree, fromdocname):
    for node in doctree.traverse():
        parent = node.parent
        text = node.astext()
        id = create_id(text)
        if id in inherits:
            position = inherits[id]['position']
            nodes = inherits[id]['nodes']
            if position == u'after':
                nodes = [node] + nodes
            elif position == u'before':
                nodes = nodes + [node]
            parent.replace(node, nodes)

def setup(app):
    app.add_config_value('inheritance_plaintext', True, 'env')
    app.add_config_value('inheritance_pattern', re.compile(r'#(.|[^#]+)#'), 'env')
    app.add_config_value('inheritance_modules', [], 'env')

    app.connect(b'builder-inited', init_transformer)
    app.connect(b'source-read', check_module)
    app.connect(b'doctree-resolved', replace_inheritances)
    app.connect(b'doctree-resolved', add_references)
