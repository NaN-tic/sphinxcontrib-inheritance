# -*- coding: utf-8 -*-
"""
    inheritance
    -----------

    :copyright: Copyright 2011-2012 by NaN Projectes de Programari Lliure, S.L.
    :license: BSD, see LICENSE for details.
"""

import pprint
import re
import sys
import unicodedata
from path import path

import docutils.nodes
import sphinx
from sphinx import addnodes
from docutils.parsers.rst import Directive
from docutils.transforms import Transform

SUPORTED_NODETYPES_POSITIONS = {
    # 'document',
    'section': ['before', 'after', 'inside'],
    'title': ['after'],
    'paragraph': ['before', 'after'],
    'block_quote': ['before', 'after'],
    'literal_block': ['before', 'after'],
    'note': ['before', 'after'],
    'tip': ['before', 'after'],
    'warning': ['before', 'after'],
    'important': ['before', 'after'],
    'bullet_list': ['before', 'after', 'inside'],
    # 'list_item',
    'figure': ['before', 'after'],
    # 'caption',
    'toctree': ['before', 'after', 'inside'],
    # 'compound',
    'comment': ['before', 'after'],
    }

existing_ids = set()
inherits = {}
inherit_types = set()


class inheritref_node(docutils.nodes.General, docutils.nodes.Element):
    pass


class inheritance_node(docutils.nodes.PreBibliographic,
        docutils.nodes.Structural, docutils.nodes.Element):
    pass


def slugify(text):
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
    text = unicode(re.sub(r'[^\w\s-]', '', text).strip().lower())
    return re.sub(r'[-\s]+', '_', text)


def get_node_type(node):
    return str(type(node)).split('.')[-1].rstrip("'>")


class InheritRef(Directive):
    has_content = True
    # required_arguments = 0
    # optional_arguments = 1
    # final_argument_witespace = False
    # option_spec = {
    #     'hola': directives.unchanged_required,
    #     }

    def run(self):
        # env = self.state.document.settings.env
        config = self.state.document.settings.env.config
        reference_pattern = config.inheritance_reference_pattern
        if isinstance(reference_pattern, basestring):
            reference_pattern = re.compile(reference_pattern)

        if not self.content or not self.content[0]:
            raise Exception("ERROR: 'inheritref' directive requires content: "
                    "'%s'" % self.content)
        ref = self.content[0]
        ref_match = reference_pattern.match(ref)
        if not ref_match:
            raise Exception("ERROR: invalid inheritref '%s'. It doesn't have "
                    "the expected format: PREFIX:NODE_TYPE:IDENTIFIER" % ref)
        nodetype = ref_match.groupdict().get('nodetype', '')
        if nodetype not in SUPORTED_NODETYPES_POSITIONS:
            raise Exception("ERROR: invalid inheritref '%s'. The node type "
                    "'%s' is not supported" % (ref, nodetype))
        if ref in existing_ids:
            raise Exception("ERROR: explicit inheritref '%s' is defined more "
                    "than one times." % ref)
        existing_ids.add(ref)
        if len(self.content) > 1:
            sys.stderr.write("WARNING: Unexpected extra content in directive "
                    "'inheritref' with ref '%s'\n" % ref)
        inheritref = inheritref_node('')
        inheritref['inheritref'] = ref
        inheritref['inheritnodetype'] = nodetype
        if config.verbose and nodetype == 'toctree':
            source = (self.state.document.attributes['source'] or '')
            sys.stderr.write("DEBUG: toctree node %s in file %s. Exists in "
                    "inheritance dict? %s.\n" % (ref, source, ref in inherits))
        return [inheritref]


class Replacer(Transform):
    default_priority = 1000

    @classmethod
    def _search_inherited_node(cls, curr_node, config):
        assert isinstance(curr_node, inheritref_node), "Unexpected type of " \
                "curr_node: %s (%s). cls: %s" % (curr_node, type(curr_node),
                    cls)
        ref = curr_node['inheritref']
        inherited_node_type = curr_node['inheritnodetype']
        node_index = curr_node.parent.index(curr_node)
        # Get next node in doctree. If 'inheritref' node is the last in current
        # "parent" (typically; section) it search in next parent brother
        while (curr_node.parent and
                (len(curr_node.parent) - 1) == node_index):
            curr_node = curr_node.parent
            node_index = curr_node.parent.index(curr_node)
        if not curr_node.parent:
            raise Exception("ERROR: inheritref node '%s' doesn't "
                    "have any next node." % ref)
        next_node = curr_node.parent[node_index + 1]
        if config.verbose:
            sys.stderr.write("DEBUG: next_node: %s. Now, I'll try to get "
                    "traverse:\n" % next_node)
        for tnode in next_node.traverse():
            if tnode.tagname == inherited_node_type:
                if config.verbose:
                    sys.stderr.write("  - %s. This is the inherited node\n"
                            % tnode)
                return tnode
            if config.verbose:
                sys.stderr.write("  - %s.\n" % tnode)
            if tnode.tagname == 'inheritref_node':
                raise Exception("Found unexpected inheritref node before "
                    "found the inherited node of previous inheritref: %s"
                    % tnode)
        if config.verbose:
            sys.stderr.write("  END traverse next_node.\n")
        if next_node.tagname == inherited_node_type:
            return next_node
        raise Exception("Invalid inheritref definition '%s'. The type of "
                "inherited node found is not the expected: %s"
                        % (ref, next_node.tagname))

    def apply(self):
        env = self.document.settings.env
        pattern = env.config.inheritance_pattern
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        def add_to_inherit_vals(inherit_vals, node):
            if not inherit_vals:
                return
            if isinstance(node, addnodes.toctree):
                node['parent'] = inherit_vals['inherited_docname']
            if node.parent:
                found = False
                p = node.parent
                inherit_children = inherit_vals['inheritance_node'].children
                while p:
                    # TODO: provably it could be improved with a traverse
                    # over current_inherit_children for nodes of type
                    # type(p)
                    if p in inherit_children:
                        found = True
                        break
                    p = p.parent
                if found:
                    return
            inherit_vals['inheritance_node'].append(node)
            # current_inherit_vals['rawsource'] += node.astext() + "\n"

        current_inherit_ref = None
        current_inherit_vals = None
        for node in self.document.traverse():
            if isinstance(node, (docutils.nodes.Inline, docutils.nodes.Text)):
                continue
            if isinstance(node, inheritref_node):
                inherit_node = Replacer._search_inherited_node(node,
                    env.config)
                inherit_node_type = node['inheritnodetype']
                node['inheritnode'] = inherit_node
                if (inherit_node_type not in ('section', 'title') or
                        node.parent.index(node) <= 1):
                    add_to_inherit_vals(current_inherit_vals, node)
                    continue
                # inheritref node introduced by inheritref directive is
                # introduced in a wrong position when nodetype is 'section' or
                # title; it's introduced as child of previous section when it
                # as previous simbling node respect inherited node
                node.parent.remove(node)
                inherit_node.parent.insert(
                    inherit_node.parent.index(inherit_node), node)
                continue

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

                if current_inherit_ref is not None:
                    self._check_inherit_vals(current_inherit_ref,
                            current_inherit_vals)

                # extract the reference data (excluding the leading dash)
                refdata = match.group(1)

                source = (node.document and node.document.attributes['source']
                    or '')
                try:
                    position, inherited_docname, nodetype, refid = \
                            refdata.split(':')
                except ValueError:
                    raise ValueError('Invalid inheritance ref "%s" at %s:%s'
                            % (refdata, source, node.line))
                if nodetype not in SUPORTED_NODETYPES_POSITIONS:
                    raise Exception('ERROR: Invalid inheritance ref "%s" at '
                            '%s:%s. The node type "%s" is not supported'
                                    % (refdata, source, node.line, nodetype))
                if position not in SUPORTED_NODETYPES_POSITIONS[nodetype]:
                    raise Exception('ERROR: Invalid inheritance ref "%s" at '
                            '%s:%s. The position "%s" is not supported for '
                            'node types "%s"' % (refdata, source, node.line,
                                position, nodetype))
                ref = '%s:%s:%s' % (inherited_docname, nodetype, refid)
                current_inherit_ref = ref

                container = inheritance_node()
                container['source'] = path(source).relpath()
                container['inheritref'] = ref
                # container['rawsource'] = inherit_vals['rawsource']

                current_inherit_vals = {
                    'inherited_docname': inherited_docname,
                    'nodetype': nodetype,
                    'position': position,
                    'inheritance_node': container,
                    'replaced': 0,
                    'source': path(source).relpath(),
                    # 'rawsource': node.astext() + "\n",
                    'line': node.line,
                    }
                inherits.setdefault(ref, []).append(current_inherit_vals)
                if env.config.verbose:
                    sys.stderr.write("Put in inherits '%s' from file %s\n"
                            % (ref, source))

                current_docname = path(source).relpath(env.srcdir)\
                    .split('.')[0]
                if env.config.verbose:
                    sys.stderr.write("-- Adding to files_to_rebuild[%s]: %s\n"
                        % (current_docname, inherited_docname))
                env.files_to_rebuild.setdefault(current_docname,
                    set()).add(inherited_docname)
                continue

            add_to_inherit_vals(current_inherit_vals, node)

        if current_inherit_ref is not None:
            self._check_inherit_vals(current_inherit_ref, current_inherit_vals)

    def _check_inherit_vals(self, inherit_ref, inherit_vals):
        config = self.document.settings.env.config

        def get_and_check_size_type(position, nodetype, node_list, min_size,
                max_size, nodetype_1st_node):
            assert ((min_size is None or len(node_list) >= min_size) and
                    (max_size is None or len(node_list) <= max_size)), \
                    "Unexpected inheritance nodes list size in '%s' '%s' " \
                    "inheritance '%s': %s\n    %s\n" % (position, nodetype,
                            inherit_ref, len(node_list), node_list)
            if len(node_list) < 1:
                return None
            assert isinstance(node_list[0], nodetype_1st_node), \
                    "Unexpected type of inheritance node in '%s' '%s' " \
                    "inheritance (%s): %s\n" % (position, nodetype,
                            inherit_ref, type(node_list))
            return node_list[0]

        inherit_children = inherit_vals['inheritance_node'].children

        if (inherit_vals['position'] == 'inside' and
                inherit_vals['nodetype'] == 'toctree'):
            inh_node = get_and_check_size_type('inside', 'toctree',
                    inherit_children, 1, 1, docutils.nodes.compound)
            inh_node = get_and_check_size_type('inside', 'toctree',
                    inh_node.children, 1, 1, sphinx.addnodes.toctree)
            inherit_vals['inheritance_node'].clear()
            inherit_vals['inheritance_node'].append(inh_node)
        elif (inherit_vals['position'] == 'inside' and
                inherit_vals['nodetype'] == 'bullet_list'):
            if config.verbose:
                sys.stderr.write("inherit_vals bullet_list: %s\n" %
                        pprint.pformat(inherit_vals, indent=2))
            inh_node = get_and_check_size_type('inside', 'bullet_list',
                    inherit_children, 1, None, docutils.nodes.bullet_list)
            if config.verbose:
                sys.stderr.write("inh_node bullet_list: %s\nchildren: %s\n"
                        % (inh_node, inh_node.children))
            # TODO: it is missing to do something?
        return


def init_transformer(app):
    env = app.builder.env
    srcdir_path = path(app.builder.env.srcdir)
    modules = app.config.inheritance_modules
    if isinstance(modules, (str, unicode)):
        modules = [x.strip() for x in modules.split(',')]
    app.config.exclude_patterns += [str(d.relpath(srcdir_path))
        for d in srcdir_path.dirs() if d.relpath(srcdir_path) not in modules]

    env.found_docs = set(d for d in env.found_docs
        if d == app.config.master_doc or d.split('/')[0] in modules)

    if app.config.inheritance_plaintext:
        app.add_transform(Replacer)


def sort_docnames(app, env, docnames):
    inheritance_modules = app.config.inheritance_modules
    if not inheritance_modules:
        return

    # inheritance modules should come ordered by inheritance dependency
    # It reverse them to read before the document that inherits than the
    # inherited document
    inheritance_modules.reverse()

    # docnames that aren't in any module. it should be only base index
    sorted_docnames = [d for d in docnames
        if d.split('/')[0] not in inheritance_modules]
    if len(sorted_docnames) > 1:
        sys.stderr.write("WARN: there are more than one docname out of "
            "inheritance modules: %s\n" % ",".join(docnames))

    # add docnames sorted by order of its module in inheritance_modules list
    sorted_docnames += [d
        for (_, d_by_m) in zip(inheritance_modules,
            [[d for d in docnames
                    if d.split('/')[0] == m]
                for m in inheritance_modules])
        for d in d_by_m]
    docnames[:] = sorted_docnames


def replace_inheritances(app, doctree):
    if app.config.verbose:
        sys.stderr.write("replace_inheritances: %s\n" % (doctree['source'], ))

    search_inheritances(app, doctree)

    if app.config.verbose:
        sys.stderr.write("  end replace_inheritances(%s):\n"
            % doctree['source'])

    # Regenerate document toc to include inherit content
    # The inheritance_modules list (in conf.py) must to be ordered by
    # inheritance dependency to ensure that here all inheritances over current
    # docname has been applied
    if app.builder.env.docname in app.builder.env.toctree_includes:
        # Avoid to duplicate content of toctree_includes[docname] when call
        # build_toc_from
        del app.builder.env.toctree_includes[app.builder.env.docname]
    app.builder.env.build_toc_from(app.builder.env.docname, doctree)


def search_inheritances(app, doctree):
    if not doctree:
        return
    for node in doctree.traverse(inheritref_node):
        inherit_node = node['inheritnode']
        if node['inheritref'] not in inherits:
            if app.config.inheritance_debug:
                sys.stderr.write("DEBUG: ref '%s' found in inheritref "
                        "directive doesn't have any inheritance.\n"
                                % node['inheritref'])
            continue
        if app.config.inheritance_debug:
            sys.stderr.write("DEBUG: inheritance_%s (%s) found\n"
                % (node['inheritref'], node['inheritnodetype']))
        apply_inheritance(app, [node, inherit_node], node['inheritref'])


def apply_inheritance(app, node_list, inheritref):
    """
    ;param node_list: two-item list with the inheritref_node + inherited node
    """
    def add_docname_to_files_to_rebuild(current_node_source,
            inherited_node_source):
        env = app.builder.env
        node_docname = path(current_node_source).relpath(env.srcdir)\
            .split('.')[0]
        inherited_docname = path(inherited_node_source).relpath(env.srcdir)\
            .split('.')[0]
        if app.config.verbose:
            sys.stderr.write("current/inherited_node_docname: %s--%s\n"
                % (node_docname, inherited_docname))

        # when document is included in toctree:
        # - there is an entry for document with toctree in env.toctree_includes
        #    with the list of documents included in toctree
        # - there is the reverse relation in files_to_rebuild: per each file
        #   included in toctree, there is an entry in files_to_rebuild with a
        #   set of documents that include it
        # Here, if inherited document is included in any toctree, it adds
        # current document in env.files_to_rebuild for all documents that
        # include inherited document
        for docname in env.files_to_rebuild.get(inherited_docname, []):
            if docname in env.toctree_includes:
                env.files_to_rebuild.setdefault(docname,
                    set()).add(node_docname)

    for n in node_list:
        if isinstance(n, (docutils.nodes.Inline, docutils.nodes.Text)):
            sys.stderr.write("WARNING: Inheritance to an unsuported Inline or "
                    "Text node. Ignored.\n")
            # if debug, more info
            return

    inherit_vals_list = inherits.get(inheritref, [])
    if not inherit_vals_list:
        return
    del inherits[inheritref]
    for inherit_vals in inherit_vals_list:
        position = inherit_vals['position']
        inheritance_container = inherit_vals['inheritance_node']

        # Search and apply inheritance inside nodes to insert
        if app.config.verbose:
            sys.stderr.write("Searching inheritances in inherited nodes: %s\n"
                % inheritance_container.__repr__())
        search_inheritances(app, inheritance_container)
        if app.config.verbose:
            sys.stderr.write("END searching inheritances in inherited nodes\n")

        if app.config.verbose:
            sys.stderr.write("inherit_vals[%s]: %s\n" % (inheritref,
                    pprint.pformat(inherit_vals)))
            sys.stderr.write("Applying inheritance %s over %s:\n"
                " - parent of node_list[0] (%s): %s\n"
                " - parent of node_list[-1] (%s): %s\n"
                % (position, inheritref,
                    type(node_list[0]), node_list[0].parent.__repr__(),
                    type(node_list[-1]), node_list[-1].parent.__repr__()))

        start_node_list_size = len(node_list)
        if position == u'after':
            inherited_node = node_list[-1]
            inherited_node.parent.insert(
                inherited_node.parent.index(inherited_node) + 1,
                inheritance_container.children)
            #    inheritance_container) it adds inheritance node which allows
            # to generate specific HTML output but it breaks
            # environment.build_toc_from() the 'traverse_in_section' part
            add_docname_to_files_to_rebuild(inherit_vals['source'],
                inherited_node.source)
        elif position == u'before':
            inherited_node = node_list[0]
            inherited_node.parent.insert(
                inherited_node.parent.index(inherited_node),
                inheritance_container.children)
            # inheritance_container) IDEM
            add_docname_to_files_to_rebuild(inherit_vals['source'],
                inherited_node.source)
        elif position == u'inside':
            if inherit_vals['nodetype'] == 'toctree':
                if app.config.verbose:
                    sys.stderr.write("container children of 'inside' "
                        "'toctree': %s\nnode_list: %s\n"
                        % (inheritance_container[0], node_list[1]))
                    sys.stderr.write("container['entries'] of 'inside' "
                        "'toctree': %s\nnode_list['entries']: %s\n"
                        % (inheritance_container[0]['entries'],
                            node_list[1]['entries']))

                node_list[1]['entries'].extend(
                    inheritance_container[0]['entries'])
                node_list[1]['includefiles'].extend(
                    inheritance_container[0]['includefiles'])
                # TODO: add_docname_to_files_to_rebuild
            elif inherit_vals['nodetype'] == 'bullet_list':
                if app.config.verbose:
                    sys.stderr.write("inheritance_container of 'inside' "
                        "'bullet_list': %s\nnode_list: %s\n"
                        % (inheritance_container[0], node_list[1]))
                    sys.stderr.write("inheritance_container.children of "
                        "'inside' 'bullet_list': %s\nnode_list.children: %s\n"
                        % (inheritance_container[0].children,
                            node_list[1].children))

                node_list[1].extend(inheritance_container[0].children)
                if len(inheritance_container) > 1:
                    node_list[-1].replace_self([node_list[-1]] +
                            inheritance_container[1:])
                    inherited_node = node_list[-1]
                    insert_index = (inherited_node.parent.index(inherited_node)
                        + 1)
                    for node in inheritance_container.children[1:]:
                        inherited_node.parent.insert(insert_index, node)
                        insert_index += 1
                add_docname_to_files_to_rebuild(inherit_vals['source'],
                    node_list[1].source)
            else:
                node_list[-1].extend(inheritance_container.children)
                # node_list[-1].append(inheritance_container) Idem
                add_docname_to_files_to_rebuild(inherit_vals['source'],
                    node_list[-1].source)

        if app.config.verbose:
            sys.stderr.write("Applied inheritance %s over %s:\n"
                " - initial len(node_list): %s, current len(node_list): %s\n"
                " - parent of container: %s\n"
                " - node_list[0].parent == container parent? %s\n"
                " - node_list[-1].parent == container parent? %s\n"
                % (position, inheritref, start_node_list_size, len(node_list),
                    inheritance_container.parent.__repr__(),
                    inheritance_container.parent == node_list[0].parent,
                    inheritance_container.parent == node_list[-1].parent))
        inherit_vals['replaced'] += 1
    return


def report_warnings(app, exception):
    if app.config.verbose and inherit_types:
        sys.stderr.write("Used inherit types:\n - %s\n"
                % "\n - ".join(inherit_types))
    if not app.config.inheritance_debug:
        return
    for key, value_list in inherits.iteritems():
        for values in value_list:
            if not values['replaced']:
                sys.stderr.write("%s:%s:: WARNING: Inheritance ref '%s' not "
                        "found.\n" % (values['source'], values['line'], key))
                continue
            sys.stderr.write('%s:%s:: "%s" was replaced %d times.\n'
                    % (values['source'], values['line'], key,
                        values['replaced']))


def visit_inheritref_node(self, node):
    inheritref = node['inheritref']
    target = docutils.nodes.target('', '', ids=[inheritref])
    node.insert(0, target)
    self.visit_target(target)
    self.depart_target(target)

    if (hasattr(self, 'settings') and
            self.settings.env.config.inheritance_debug):
        abbrnode = sphinx.addnodes.abbreviation('[+id]', '[+id]',
            explanation=inheritref)
        self.visit_abbreviation(abbrnode)
        self.body.append('[+id]')
        self.depart_abbreviation(abbrnode)


def depart_inheritref_node(self, node):
    pass


def visit_inheritance_node(self, node):
    self.body.append(self.starttag(node, 'span', '', CLASS='inheritance',
            DATA_SOURCE=node['source'], DATA_INHERITREF=node['inheritref']))
    self.context.append('</span>')


def depart_inheritance_node(self, node):
    self.body.append(self.context.pop())


def visit_nothing(self, node):
    pass


def depart_nothing(self, node):
    pass


def setup(app):
    app.add_config_value('inheritance_plaintext', True, 'env')
    app.add_config_value('inheritance_pattern', re.compile(r'^#\:(.|[^#]+)#$'),
            'env')
    app.add_config_value('inheritance_reference_pattern',
            re.compile(r'(?P<prefix>[a-zA-Z/_0-9]+):(?P<nodetype>[a-z_]+):'
                    '(?P<identifier>[a-zA-Z0-9]+)'), 'env')
    app.add_config_value('inheritance_modules', [], 'env')
    app.add_config_value('inheritance_debug', False, 'env')
    app.add_config_value('verbose', False, 'env')

    app.add_node(inheritref_node,
        html=(visit_inheritref_node, depart_inheritref_node),
        latex=(visit_nothing, depart_nothing),
        text=(visit_nothing, depart_nothing),
        man=(visit_nothing, depart_nothing),
        texinfo=(visit_nothing, depart_nothing))
    app.add_node(inheritance_node,
        html=(visit_inheritance_node, depart_inheritance_node),
        latex=(visit_nothing, depart_nothing),
        text=(visit_nothing, depart_nothing),
        man=(visit_nothing, depart_nothing),
        texinfo=(visit_nothing, depart_nothing))

    app.add_directive('inheritref', InheritRef)

    app.connect(b'builder-inited', init_transformer)
    app.connect(b'env-before-read-docs', sort_docnames)
    app.connect(b'doctree-read', replace_inheritances)
    app.connect(b'build-finished', report_warnings)
