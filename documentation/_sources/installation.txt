Installation
============



Supported Installation Methods
-------------------------------

MongoTor supports installation using standard Python "distutils" or
"setuptools" methodologies. An overview of potential setups is as follows:

Install via easy_install or pip
-------------------------------

When ``easy_install`` or ``pip`` is available, the distribution can be 
downloaded from Pypi and installed in one step::

    easy_install mongotor

Or with pip::

    pip install mongotor

This command will download the latest version of MongoTor from the `Python
Cheese Shop <http://pypi.python.org/pypi/mongotor>`_ and install it to your system.

Installing using setup.py
----------------------------------

Otherwise, you can install from the distribution using the ``setup.py`` script::

    python setup.py install

Checking the Installed MongoTor Version
---------------------------------------------

The version of MongoTor installed can be checked from your
Python prompt like this:

.. sourcecode:: python

     >>> import mongotor 
     >>> mongotor.version # doctest: +SKIP

Requirements
------------

The following three python libraries are required.

  * `pymongo <http://github.com/mongodb/mongo-python-driver>`_ version 1.9+ for bson library
  * `tornado <http://github.com/facebook/tornado>`_

.. note::
   The above requirements are automatically managed when installed using
   any of the supported installation methods