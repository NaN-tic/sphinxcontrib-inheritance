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

In order to use inheritance you should add it to the list of extensions in conf.py::

   extensions = ['sphinxcontrib.inheritance']

You should also add the list of modules that should be processed::

   inheritance_modules = 'submodule1, submodule2'

or::

   inheritance_modules = ['submodule1', 'submodule2']

Usage
-----

Given an existing sphinx project, you can add text from a new module in the following way:

* Create a subdirectory in the project. For example *submodule1*.
* Add this directory to inheritance_modules if it must be built.
* Create any number of .rst files in the directory with the following syntax::

   #:after:identifier_of_existing_paragraph#

   This is the text to be included after the existing paragraph.

   As well as any other text until the next #::# directive or the end of file.

And that's it. The text provided will be added after the mentioned paragraph. 
Possible positions accepted by the extension are:

* *after* which adds the supplied paragraph after the referenced one
* *before* which adds the supplied paragraph before the referenced one
* *replace* which replaces the referenced paragraph with the text provided.
Files containing inheritance information can be in subdirectories of the main one.

A paragraph's identifier is automatically created by the system by replacing 
spaces and other non-ascii charaters by "**_**" and picking only the first 7 words
of the paragraph. If two paragraphs would result in the same identifier a
number will be appended to ensure it is unique.

Currently, the only way to see this ID is taking a look at the HTML code 
generated and see what 'id' attribute has been given to the paragraph or 
section. Note that this means that this extension adds anchors to *all* rst
elements (except inline directives) and thus you can access to 
*filename.html#identifier_of_existing_paragraph*.

