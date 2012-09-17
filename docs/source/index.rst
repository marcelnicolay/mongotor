==========================================
Welcome to Mongotor's documentation!
==========================================

(MONGO + TORnado) is an asynchronous toolkit for accessing mongo with tornado.

Features
========

    * ORM like to map documents and fields :py:mod:`~mongotor.orm`
    * Advanced connection management (replica sets, slave okay)
    * Automatic reconnection
    * Connection pooling
    * Support for running database commands (find, find_one, count, sum, mapreduce etc...)
    * Signals for pre_save, post_save, pre_remove, post_remove, pre_update and post_update
    * 100% of code coverage by test

Contents:
=========

.. toctree::
   :maxdepth: 2

   installation
   tutorial
   api/index


Contributing to the project
===========================

`List of contributors <https://github.com/marcelnicolay/mongotor/contributors>`_

Source Code
-----------

The source is available on `GitHub <https://github.com/marcelnicolay/mongotor>`_ and contributions are welcome.

Issues
------

Please report any issues via `github issues <https://github.com/marcelnicolay/mongotor/issues>`_


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
