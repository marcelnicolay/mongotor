# coding: utf-8
# <mongotor - mongodb asynchronous toolkit built on top of tornado >
# Copyright (C) <2012>  Marcel Nicolay <marcel.nicolay@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
from tornado import gen
from mongotor.pool import ConnectionPool


class Database(object):
    """Database object
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls)

        return cls._instance

    def init(self, addresses, dbname, **kwargs):
        self._addresses = addresses
        self._dbname = dbname

        self._pool = ConnectionPool(addresses, dbname, **kwargs)

    def get_collection_name(self, collection):
        return u'%s.%s' % (self._dbname, collection)

    @classmethod
    def connect(cls, addresses, dbname, **kwargs):
        """Connect to database

        :Parameters:
          - `addresses` :
          - `dbname` : database name
          - `kwargs` : kwargs passed to connection pool
        """
        if cls._instance:
            raise ValueError('Database already intiated')

        database = Database()
        database.init(addresses, dbname, **kwargs)

        return database

    @classmethod
    def disconnect(cls):
        if not cls._instance:
            raise ValueError("Database isn't connected")

        cls._instance._pool.close()
        cls._instance = None

    @gen.engine
    def send_message(self, message, callback=None):

        connection = yield gen.Task(self._pool.connection)
        try:
            connection.send_message(message, callback=callback)
        except:
            connection.close()
            raise
