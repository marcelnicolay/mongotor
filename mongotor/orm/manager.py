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
from mongotor.database import Database


class Manager(object):

    def __init__(self, collection):
        self.collection = collection

    @gen.engine
    def find_one(self, query, callback):
        result, error = yield gen.Task(
            Database(self.collection.__collection__).find_one, query)

        instance = None
        if result and result[0]:
            instance = self.collection.create(result[0])

        callback(instance)

    @gen.engine
    def find(self, query, callback, **kw):
        result, error = yield gen.Task(
            Database(self.collection.__collection__).find, query, **kw)
        items = []

        if result and result[0]:
            for item in result[0]:
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
        if result and len(result) > 0 and 'n' in result[0]:
            total = int(result[0]['n'])

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
        if error['error'] or not result or not result[0]['ok']:
            callback(None)
            return

        callback(result[0]['values'])

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

        if result:
            if result[0]['retval']:
                total = result[0]['retval'][0]['csum']

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

        if result:
            if result[0]['ok']:
                for item in result[0]['results']:
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
        if not result or int(result[0]['ok']) != 1:
            callback(None)
            return

        callback(result[0]['results'])

    @gen.engine
    def drop(self, callback):
        yield gen.Task(Database(self.collection.__collection__).remove)

        callback()
