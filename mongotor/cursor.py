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
from mongotor import message


class Cursor(object):

    def __init__(self, dbname, collection, pool):
        self._dbname = dbname
        self._collection = collection
        self._pool = pool

    @property
    def collection_name(self):
        return u'%s.%s' % (self._dbname, self._collection)

    @gen.engine
    def insert(self, docs, check_keys=True, safe=True,
        callback=None, **kwargs):

        if isinstance(docs, dict):
            docs = [docs]

        assert isinstance(docs, list)

        connection = yield gen.Task(self._pool.connection)
        try:
            message_insert = message.insert(self.collection_name, docs,
                check_keys, safe, kwargs)

            connection.send_message(message_insert, callback=callback)
        except:
            connection.close()
            raise

    @gen.engine
    def remove(self, spec_or_id=None, safe=True, callback=None, **kwargs):
        if spec_or_id is None:
            spec_or_id = {}
        if not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        connection = yield gen.Task(self._pool.connection)
        try:
            message_delete = message.delete(self.collection_name, spec_or_id,
                safe, kwargs)
            connection.send_message(message_delete, callback=callback)
        except:
            connection.close()
            raise

    @gen.engine
    def update(self, spec, document, upsert=False, safe=True,
        multi=False, callback=None, **kwargs):
        """Update a document(s) in this collection.
        """

        connection = yield gen.Task(self._pool.connection)
        try:
            message_update = message.update(self.collection_name, upsert,
                multi, spec, document, safe, kwargs)
            connection.send_message(message_update, callback=callback)
        except:
            connection.close()
            raise
