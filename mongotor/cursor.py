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
from bson import SON
from mongotor import message
from mongotor.database import Database


_QUERY_OPTIONS = {
    "tailable_cursor": 2,
    "slave_okay": 4,
    "oplog_replay": 8,
    "no_timeout": 16}

DESCENDING = -1
ASCENDING = 1


class Cursor(object):
    """A cursor / iterator over Mongo query results.
    """

    def __init__(self, collection, spec=None, fields=None, snapshot=False,
        tailable=False, max_scan=None, is_command=False, explain=False,
        hint=None, timeout=True):

        if spec is not None and not isinstance(spec, dict):
            spec = {"_id": spec}

        self._spec = spec or {}
        self._fields = fields
        self._snapshot = snapshot
        self._tailable = tailable
        self._max_scan = max_scan
        self._hint = hint
        self._collection = collection
        self._collection_name = Database().get_collection_name(collection)
        self._timeout = timeout
        self._is_command = is_command
        self._explain = explain

    @gen.engine
    def find(self, skip=0, limit=0, sort=None, callback=None):
        self._ordering = sort

        message_query = message.query(self._query_options(), self._collection_name,
            skip, limit, self._query_spec(), self._fields)

        response, error = yield gen.Task(Database().send_message, message_query)

        # close cursor
        if response and response.get('cursor_id'):
            cursor_id = response['cursor_id']
            Database().send_message(message.kill_cursors([cursor_id]), callback=None)

        if error:
            callback((None, error))
        else:
            if limit == -1 and len(response['data']) == 1:
                callback((response['data'][0], None))
            else:
                callback((response['data'], None))

    def _query_options(self):
        """Get the query options string to use for this query."""
        options = 0
        if self._tailable:
            options |= _QUERY_OPTIONS["tailable_cursor"]
        if not self._timeout:
            options |= _QUERY_OPTIONS["no_timeout"]
        return options

    def _query_spec(self):
        """Get the spec to use for a query."""
        spec = self._spec
        if not self._is_command and "$query" not in self._spec:
            spec = SON({"$query": self._spec})
        if self._ordering:
            spec["$orderby"] = self._ordering
        if self._explain:
            spec["$explain"] = True
        if self._hint:
            spec["$hint"] = self._hint
        if self._snapshot:
            spec["$snapshot"] = True
        if self._max_scan:
            spec["$maxScan"] = self._max_scan
        return spec
