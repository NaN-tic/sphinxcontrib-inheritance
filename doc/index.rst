Inheritance documentation
=========================

What is it?
-----------

Inheritance adds the possibility of extending an existing sphinx project
without the need of adding any kind of directives or hooks to the original
document.

It's been designed for projects that make an extensive use of pluggable modules
such as Tryton and will work correctly with TryDoc, another sphinx extension
that helps in writing documentation for Tryton modules.


Installation
------------

This extension requires the following packages:

- Sphinx 1.0

Use ``pip`` to install this extension straight from the Python Package Index::

   pip install sphinx-inheritance


Configuration
-------------

In order to use inheritance you should add it to the list of extensions in
conf.py::

   extensions = ['sphinxcontrib.inheritance']

You should also add the list of modules that should be processed::

   inheritance_modules = 'submodule1, submodule2'

or::

   inheritance_modules = ['submodule1', 'submodule2']

Other important configuration options for inheritance are::

    inheritance_debug = False
    verbose = False

These aren't required and these are the default values. The use of these
options are detailed in the next section.


Usage
-----

Given an existing sphinx project, you can add text from a new module in the
following way:

* Create a subdirectory in the project. For example *submodule1*.
* Add this directory to inheritance_modules if it must be built.
* Create any number of .rst files in the directory with the following syntax::

   #:after:module/file:paragraph:identifier_of_existing_paragraph#

   This is the text to be included after the existing paragraph.

   As well as any other text until the next #::# directive or the end of file.

And that's it. The text provided will be added after the mentioned node.

The first line is the **inherit reference**, which indicates the part of
previously existing document that will be modified by this inheritance and how
will be done.

The inherit reference consist in four parameters separated by ':'. First one is
the **position** which indicates how the current text will be included in the
base document. Possible positions accepted by the extension are:

* *after* which adds the supplied content after the referenced node
* *before* which adds the supplied content before the referenced node
* *replace* (not implemented yet) which replaces the referenced node with the
  supplied content.
* *inside* which append the supplied content to the referenced node's content

The second parameter references the **inherited source file** where is the
referenced node and the file should have the '.rst' extension removed.

The third is the **node type**. This is the list of suported node
types:

* section
* title
* paragraph
* block_quote
* literal_block
* note
* tip
* warning
* important
* bullet_list
* figure (only with explicit references)
* toctree (only with explicit references)
* comment

The last parameter is the **identifier of existing node**. It could be a part
or little summary about referenced node, or a less content-dependant
identifier.

The inherit references must to be defined explicitly with the **inheritref**
directive.


Defining an inherit references
******************************

This is an example of use of **inheritref** directive::

    .. inheritref:: trytond_doc/maestro:title:maestros

The anatomy of inherit references explained above is required even if you
define them explicitly. In this case, the *inherited source file* parameter is
not used, but it's recommended to reference the real source file to make easy
to locate the referenced node for humans.

However, for the *identifier of existing node* is recommended to choose one
wiche will be robust to changes in text, to be them more inmutable and
persistent throw future versions of documentation (it is the main reason to use
explicit inherit references).

If an inheritance is not applied or not as you expect, setting true the
**inheritance_debug** option in *conf.py* file will help you. If you found a
bug, provably the **verbose** option will help you to found the solution.


Restrictions in position usage
******************************

There are some combinations of inherited node type and position. *after*,
*before* and *replace* are allowed for all node types except *before*, which
can't be used with *title* node type (it doesn't make sense insert content
before the **title** node which is always the first node of a *section*).

The *inside* position is allowed only for node types *section* (append any
content at the end of section's content) and *bullet_list* or *toctree* (the
inheritance content must to be also a **bullet_list** or *toctree* respectively
and it will append its items to the inherited list).


Tips
****

Given that sphinx-build only re-reads files which have changed, you'll probably
want to use the *-E* parameter to ensure all files are read on each build. The
reason is that if one of the files changed must alter the structure of a
non-modified one, the changes will take no efect. If you use the standard
sphinx Makefile you can modify the *SPHINXBUILD* variable like this::

   SPHINXBUILD   = sphinx-build -E

