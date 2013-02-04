# -*- coding: utf-8 -*-
"""
    inheritance
    -----------

    :copyright: Copyright 2011-2012 by NaN Projectes de Programari Lliure, S.L.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import unicodedata

#from docutils import nodes
from docutils.transforms import Transform

import sphinx
#from sphinx.locale import _
#from sphinx.environment import NoUri
#from sphinx.util.compat import Directive
#from docutils.parsers.rst import directives, states
import docutils.nodes 


def slugify(text):                                                             
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')      
    text = unicode(re.sub('[^\w\s-]', '', text).strip().lower())              
    return re.sub('[-\s]+', '_', text)

def get_node_type(node):
    return str(type(node)).split('.')[-1].rstrip("'>")

existing_ids = set()

def create_id(node):
    found = False
    value = node.astext()
    value = value.replace('[+id]', '')
    value = value.strip()
    node_type = get_node_type(node)
    source = node.document and node.document.attributes['source'] or ''
    splitted = source.split(os.path.sep)
    if len(splitted) >= 2:
        prefix = '%s/%s' % (splitted[-2], splitted[-1].rstrip('.rst'))
    else:
        prefix = ''
    word_count = 7
    while True:
        words = slugify(value)
        words = words.replace(':','_')
        words = words.replace('.','_')
        words = words.replace('_',' ')
        words = words.split()
        identifier = '_'.join(words[:word_count])
        identifier = '%s:%s:%s' % (prefix, node_type, identifier)

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

    # TODO: By now we do not want the identifier to change because create_id()
    # is called more than once. We need to find a better solution for creating
    # the paragraph ID.
    #existing_ids.add(identifier)
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
            if isinstance(node, (docutils.nodes.Inline, docutils.nodes.Text)):
                continue
            parent = node.parent
            text = node.astext()
            match = pattern.search(text)
            if match:
                if node.line is None:
                    continue
                # catch invalid pattern with too many groups
                if len(match.groups()) != 1:
                    raise ValueError(
                        'inherit_issue_pattern must have '
                        'exactly one group: {0!r}'.format(match.groups()))

                # extract the reference data (excluding the leading dash)
                refdata = match.group(1)

                source = (node.document and node.document.attributes['source'] 
                    or '')
                try:
                    id, position, refsource, reftype, refid = (
                        refdata.split(':'))
                except ValueError:
                    raise ValueError('Invalid inheritance ref "%s" at %s:%s' % (
                            refdata, source, node.line))
                ref = '%s:%s:%s' % (refsource, reftype, refid)
                current_inherit_ref = ref
                current_inherit_vals = {
                    'position': position,
                    'nodes': [],
                    'replaced': 0,
                    'source': source,
                    'line': node.line,
                    }
                inherits.setdefault(ref, []).append(current_inherit_vals)
                if parent:
                    parent.replace(node, [])
                continue

            if current_inherit_ref:
                if parent:
                    found = False
                    p = parent
                    while p:
                        if p in current_inherit_vals['nodes']:
                            found = True
                            break
                        p = p.parent
                    if found:
                        continue
                current_inherit_vals['nodes'].append(node)

def init_transformer(app):
    if app.config.inheritance_plaintext:
        app.add_transform(Replacer)

def add_references(app, doctree, fromdocname):
    for node in doctree.traverse():
        if isinstance(node, (docutils.nodes.Inline, docutils.nodes.Text)):
            # We do not want to consider inline nodes such as emphasis, 
            # strong or literal. Nor Text nodes which are the part of the 
            # paragraph that precede an inline node. There's already the 
            # Paragraph node and the anchor is added to it.
            continue
        if not node.parent:
            continue

        targetid = create_id(node)
        node_list = []
        node_list.append(docutils.nodes.target('', '', ids=[targetid]))
        if app.config.inheritance_debug:
            abbrnode = sphinx.addnodes.abbreviation('[+id]', '[+id]', 
                explanation=targetid)
            node_list.append(abbrnode)
        node_list.append(node)
        node.parent.replace(node, node_list)

def apply_inheritance(app, node):
    if isinstance(node, (docutils.nodes.Inline, docutils.nodes.Text)):
        return
    parent = node.parent
    #text = node.astext()
    #source = node.document and node.document.attributes['source'] or ''
    id = create_id(node)
    for inherit_vals in inherits.get(id, []):
        # aquest debug falla
        position = inherit_vals['position']
        nodes = inherit_vals['nodes']
        for n in nodes:
            for sn in n.traverse():
                apply_inheritance(app, sn)
        if position == u'after':
            nodes.insert(0, node)
        elif position == u'before':
            nodes.append(node)
        # aquest debug falla
        parent.replace(node, nodes)
        inherit_vals['replaced'] += 1

def replace_inheritances(app, doctree, fromdocname):
    for node in doctree.traverse():
        apply_inheritance(app, node)
    # regenerate the ToC of each page.
    # TODO: it could be improved generating only for modified pages in
    # inheritance
    app.builder.env.build_toc_from(fromdocname, doctree)

def report_warnings(app, exception):
    for key, value_list in inherits.iteritems():
        for values in value_list:
            if not values['replaced']:
                sys.stderr.write("%s:%s:: WARNING: Inheritance ref '%s' not "
                        "found.\n" % (values['source'], values['line'], key))
                continue
            if app.config.inheritance_debug:
                sys.stderr.write('%s:%s:: "%s" was replaced %d times.\n'
                        % (values['source'], values['line'], key,
                            values['replaced']))

def setup(app):
    app.add_config_value('inheritance_plaintext', True, 'env')
    app.add_config_value('inheritance_pattern', re.compile(r'#(.|[^#]+)#'), 
        'env')
    app.add_config_value('inheritance_modules', [], 'env')
    app.add_config_value('inheritance_debug', False, 'env'), 

    app.connect(b'builder-inited', init_transformer)
    app.connect(b'source-read', check_module)
    app.connect(b'doctree-resolved', replace_inheritances)
    app.connect(b'doctree-resolved', add_references)
    app.connect(b'build-finished', report_warnings)
