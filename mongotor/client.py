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
from mongotor.node import Node, ReadPreference
from mongotor.cursor import Cursor
from mongotor import message


class Client(object):

    def __init__(self, database, collection):
        self._database = database
        self._collection = collection
        self._collection_name = database.get_collection_name(collection)

    @gen.engine
    def insert(self, doc_or_docs, safe=True, check_keys=True, callback=None):
        """Insert a document

        :Parameters:
          - `doc_or_docs`: a document or list of documents to be
            inserted
          - `safe` (optional): check that the insert succeeded?
          - `check_keys` (optional): check if keys start with '$' or
            contain '.', raising :class:`~pymongo.errors.InvalidName`
            in either case
          - `callback` : method which will be called when save is finished
        """
        if isinstance(doc_or_docs, dict):
            doc_or_docs = [doc_or_docs]

        assert isinstance(doc_or_docs, list)

        message_insert = message.insert(self._collection_name, doc_or_docs,
            check_keys, safe, {})

        response, error = yield gen.Task(self._database.send_message,
            message_insert, read_preference=ReadPreference.PRIMARY)

        if callback:
            callback((response, error))

    @gen.engine
    def remove(self, spec_or_id={}, safe=True, callback=None):
        """remove a document

        :Parameters:
        - `spec_or_id`: a query or a document id
        - `safe` (optional): safe insert operation
        - `callback` : method which will be called when save is finished
        """
        if not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        assert isinstance(spec_or_id, dict)

        message_delete = message.delete(self._collection_name, spec_or_id,
            safe, {})

        response, error = yield gen.Task(self._database.send_message,
            message_delete, read_preference=ReadPreference.PRIMARY)

        if callback:
            callback((response, error))

    @gen.engine
    def update(self, spec, document, upsert=False, safe=True,
        multi=False, callback=None):
        """Update a document(s) in this collection.

        :Parameters:
          - `spec`: a ``dict`` or :class:`~bson.son.SON` instance
            specifying elements which must be present for a document
            to be updated
          - `document`: a ``dict`` or :class:`~bson.son.SON`
            instance specifying the document to be used for the update
            or (in the case of an upsert) insert - see docs on MongoDB
            `update modifiers`_
          - `upsert` (optional): perform an upsert if ``True``
          - `safe` (optional): check that the update succeeded?
          - `multi` (optional): update all documents that match
            `spec`, rather than just the first matching document. The
            default value for `multi` is currently ``False``, but this
            might eventually change to ``True``. It is recommended
            that you specify this argument explicitly for all update
            operations in order to prepare your code for that change.
        """
        assert isinstance(spec, dict), "spec must be an instance of dict"
        assert isinstance(document, dict), "document must be an instance of dict"
        assert isinstance(upsert, bool), "upsert must be an instance of bool"
        assert isinstance(safe, bool), "safe must be an instance of bool"

        message_update = message.update(self._collection_name, upsert,
                multi, spec, document, safe, {})

        response, error = yield gen.Task(self._database.send_message,
            message_update, read_preference=ReadPreference.PRIMARY)

        callback((response, error))

    @gen.engine
    def find_one(self, spec_or_id=None, **kwargs):
        """Get a single document from the database.

        All arguments to :meth:`find` are also valid arguments for
        :meth:`find_one`, although any `limit` argument will be
        ignored. Returns a single document, or ``None`` if no matching
        document is found.

        :Parameters:

          - `spec_or_id` (optional): a dictionary specifying
            the query to be performed OR any other type to be used as
            the value for a query for ``"_id"``.

          - `**kwargs` (optional): any additional keyword arguments
            are the same as the arguments to :meth:`find`.
        """
        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        self.find(spec_or_id, limit=-1, **kwargs)

    @gen.engine
    def find(self, *args, **kwargs):
        """Query the database.

        The `spec` argument is a prototype document that all results
        must match. For example:

        :Parameters:
          - `spec` (optional): a SON object specifying elements which
            must be present for a document to be included in the
            result set
          - `fields` (optional): a list of field names that should be
            returned in the result set ("_id" will always be
            included), or a dict specifying the fields to return
          - `skip` (optional): the number of documents to omit (from
            the start of the result set) when returning the results
          - `limit` (optional): the maximum number of results to
            return
          - `timeout` (optional): if True, any returned cursor will be
            subject to the normal timeout behavior of the mongod
            process. Otherwise, the returned cursor will never timeout
            at the server. Care should be taken to ensure that cursors
            with timeout turned off are properly closed.
          - `snapshot` (optional): if True, snapshot mode will be used
            for this query. Snapshot mode assures no duplicates are
            returned, or objects missed, which were present at both
            the start and end of the query's execution. For details,
            see the `snapshot documentation
            <http://dochub.mongodb.org/core/snapshot>`_.
          - `tailable` (optional): the result of this find call will
            be a tailable cursor - tailable cursors aren't closed when
            the last data is retrieved but are kept open and the
            cursors location marks the final document's position. if
            more data is received iteration of the cursor will
            continue from the last document received. For details, see
            the `tailable cursor documentation
            <http://www.mongodb.org/display/DOCS/Tailable+Cursors>`_.
          - `sort` (optional): a list of (key, direction) pairs
            specifying the sort order for this query. See
            :meth:`~pymongo.cursor.Cursor.sort` for details.
          - `max_scan` (optional): limit the number of documents
            examined when performing the query
          - `read_preferences` (optional): The read preference for
            this query.
        """
        callback = kwargs['callback']
        del kwargs['callback']

        cursor = Cursor(database=self._database, collection=self._collection,
            *args, **kwargs)
        cursor.find(callback=callback)
