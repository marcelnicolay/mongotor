# coding: utf-8
# <mongotor - An asynchronous driver and toolkit for accessing MongoDB with Tornado>
# Copyright (C) <2012>  Marcel Nicolay <marcel.nicolay@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from tornado import gen
from bson import SON
from mongotor import message

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

    def __init__(self, spec_or_id=None, collection=None, database=None, fields=None, snapshot=False,
        tailable=False, max_scan=None, is_command=False, explain=False, hint=None,
        skip=0, limit=0, sort=None, connection=None,
        read_preference=None, timeout=True, slave_okay=True):

        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        self._spec = spec_or_id or {}
        self._fields = fields
        self._snapshot = snapshot
        self._tailable = tailable
        self._max_scan = max_scan
        self._hint = hint
        self._database = database
        self._collection = collection
        self._collection_name = database.get_collection_name(collection)
        self._timeout = timeout
        self._is_command = is_command
        self._explain = explain
        self._slave_okay = slave_okay
        self._read_preference = read_preference
        self._connection = connection
        self._ordering = sort
        self._skip = skip
        self._limit = limit

    @gen.engine
    def find(self, callback=None):
        message_query = message.query(self._query_options(), self._collection_name,
            self._skip, self._limit, self._query_spec(), self._fields)

        if self._connection:
            response, error = yield gen.Task(self._connection.send_message, message_query)
        else:
            response, error = yield gen.Task(self._database.send_message, message_query,
                read_preference=self._read_preference)

        # close cursor
        if response and response.get('cursor_id'):
            cursor_id = response['cursor_id']

            if self._connection:
                self._connection.send_message(message.kill_cursors([cursor_id]), callback=None)
            else:
                self._database.send_message(message.kill_cursors([cursor_id]),
                    callback=None)

        if error:
            callback((None, error))
        else:
            if self._limit == -1 and len(response['data']) == 1:
                callback((response['data'][0], None))
            else:
                callback((response['data'], None))

    def _query_options(self):
        """Get the query options string to use for this query."""
        options = 0
        if self._tailable:
            options |= _QUERY_OPTIONS["tailable_cursor"]
        if self._slave_okay:
            options |= _QUERY_OPTIONS["slave_okay"]
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
