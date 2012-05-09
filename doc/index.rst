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

This extensiono

Files containing inheritance information can be in subdirectories of the main one.
