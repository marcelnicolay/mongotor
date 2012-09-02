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
from bson.son import SON
from tornado import gen
from mongotor import message
from mongotor.database import Database
from mongotor.cursor import Cursor


class Manager(object):

    def __init__(self, collection):
        self.collection = collection

    @gen.engine
    def find_one(self, query, callback):

        cursor = Cursor(self.collection.__collection__, query)
        result, error = yield gen.Task(cursor.find, limit=-1)

        instance = None
        if result:
            instance = self.collection.create(result)

        callback(instance)

    @gen.engine
    def find(self, query, callback, **kw):
        cursor = Cursor(self.collection.__collection__, query)
        result, error = yield gen.Task(cursor.find, **kw)

        items = []

        if result:
            for item in result:
                items.append(self.collection.create(item))

        callback(items)

    @gen.engine
    def count(self, query=None, callback=None):
        command = {
            "count": self.collection.__collection__
        }

        if query:
            command["query"] = query

        result, error = yield gen.Task(Database().command, command)

        total = 0
        if result and len(result) > 0 and 'n' in result:
            total = int(result['n'])

        callback(total)

    @gen.engine
    def distinct(self, key, callback, query=None):
        """Returns a list of distinct values for the given
        key across collection"""
        command = {
            "distinct": self.collection.__collection__,
            "key": key,
        }
        if query:
            command['query'] = query

        result, error = yield gen.Task(Database().command, command)

        if result and result['ok']:
            callback(result['values'])
        else:
            callback(None)

    @gen.engine
    def sum(self, query, field, callback):
        command = {
            "group": {
                'ns': self.collection.__collection__,
                'cond': query,
                'initial': {'csum': 0},
                '$reduce': 'function(obj,prev){prev.csum+=obj.' + field + ';}'
            }
        }

        result, error = yield gen.Task(Database().command, command)
        total = 0

        if result and result['retval']:
            total = result['retval'][0]['csum']

        callback(total)

    @gen.engine
    def geo_near(self, near, max_distance=None, num=None, spherical=None,
        unique_docs=None, query=None, callback=None, **kw):

        command = SON({"geoNear": self.collection.__collection__})

        if near != None:
            command.update({'near': near})

        if query != None:
            command.update({'query': query})

        if num != None:
            command.update({'num': num})

        if max_distance != None:
            command.update({'maxDistance': max_distance})

        if unique_docs != None:
            command.update({'uniqueDocs': unique_docs})

        if spherical != None:
            command.update({'spherical': spherical})

        result, error = yield gen.Task(Database().command, command)
        items = []

        if result and result['ok']:
            for item in result['results']:
                items.append(self.collection.create(item['obj']))

        callback(items)

    @gen.engine
    def map_reduce(self, map_, reduce_, callback, query=None, out=None):
        command = SON({'mapreduce': self.collection.__collection__})

        command.update({
            'map': map_,
            'reduce': reduce_,
        })

        if query is not None:
            command.update({'query': query})
        if out is None:
            command.update({'out': {'inline': 1}})

        result, error = yield gen.Task(Database().command, command)
        if not result or int(result['ok']) != 1:
            callback(None)
            return

        callback(result['results'])

    @gen.engine
    def truncate(self, callback=None):
        collection_name = Database().get_collection_name(self.collection.__collection__)
        message_delete = message.delete(collection_name, {}, True, {})

        yield gen.Task(Database().send_message, message_delete)

        if callback:
            callback()
