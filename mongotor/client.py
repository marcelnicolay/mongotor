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
from mongotor.node import Node, ReadPreference
from mongotor.errors import DatabaseError
from mongotor import message


class Client(object):

    def __init__(self, database, collection):
        self._database = database
        self._collection = collection
        self._collection_name = database.get_collection_name(collection)

    @gen.engine
    def insert(self, document, safe=True, callback=None):
        """Insert a document

        :Parameters:
        - `safe` (optional): safe insert operation
        - `callback` : method which will be called when save is finished
        """
        if isinstance(document, dict):
            document = [document]

        assert isinstance(document, list)

        message_insert = message.insert(self._collection_name, document,
            True, safe, {})

        response, error = yield gen.Task(self._database.send_message,
            message_insert, ReadPreference.PRIMARY)

        if callback:
            callback((response, error))
