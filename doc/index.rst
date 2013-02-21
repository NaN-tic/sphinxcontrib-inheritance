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

Usage
-----

Given an existing sphinx project, you can add text from a new module in the
following way:

* Create a subdirectory in the project. For example *submodule1*.
* Add this directory to inheritance_modules if it must be built.
* Create any number of .rst files in the directory with the following syntax::

   #:after:module/file:node_type:identifier_of_existing_paragraph#

   This is the text to be included after the existing paragraph.

   As well as any other text until the next #::# directive or the end of file.

And that's it. The text provided will be added after the mentioned node.
Possible positions accepted by the extension are:

* *after* which adds the supplied node after the referenced one
* *before* which adds the supplied node before the referenced one
* *replace* which replaces the referenced node with the text provided.

Files containing inheritance information can be in subdirectories of the main
one. And 'file' should have the '.rst' extension removed.

*node_type* examples are *paragraph*, *title* or *section*. Note that a section
and its title may have the same identifier but replacing the section replaces
the title and all the paragraphs in the section. The same applies to the
*after* position. Using *after* on a *title* implies that the new node will be
the first in the *section*, wheareas using it with a *section* it means it will
go after the last paragraph of the section.

A node's identifier is automatically created by the system by replacing
spaces and other non-ascii charaters by "**_**" and picking only the first 7
words of the node.

There are two ways of knowing this ID:

* Taking a look at the HTML code generated and see what 'id' attribute has been
given to the paragraph or section. Note that this means that this extension adds
anchors to *all* rst elements (except inline directives) and thus you can access
to *filename.html#identifier_of_existing_paragraph*.

* Adding the configuration value *inheritance_debug* in your *conf.py*. That
will add a *[+id]* on each paragraph (or item which can be hooked to) and it
will display a tooltip on hover with the type of element (such as Paragraph,
Title or Section) followed by the identifier. Note that this approach is only
valid for HTML output.

Given that sphinx-build only re-reads files which have changed, you'll probably
want to use the *-E* parameter to ensure all files are read on each build. The
reason is that if one of the files changed must alter the structure of a
non-modified one, the changes will take no efect. If you use the standard
sphinx Makefile you can modify the *SPHINXBUILD* variable like this::

   SPHINXBUILD   = sphinx-build -E

