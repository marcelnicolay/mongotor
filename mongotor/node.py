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

import logging
import random
from tornado import gen
from bson import SON
from mongotor.pool import ConnectionPool
from mongotor.errors import InterfaceError

logger = logging.getLogger(__name__)


class Node(object):
    """Node of database cluster
    """

    def __init__(self, host, port, database, pool_kargs=None):
        if not pool_kargs:
            pool_kargs = {}

        assert isinstance(host, (str, unicode))
        assert isinstance(port, int)

        self.host = host
        self.port = port
        self.database = database
        self.pool_kargs = pool_kargs

        self.is_primary = False
        self.is_secondary = False
        self.available = False
        self.initialized = False

        self.pool = ConnectionPool(self.host, self.port, self.database.dbname,
            **self.pool_kargs)

    @gen.engine
    def config(self, callback=None):
        ismaster = SON([('ismaster', 1)])

        response = None
        try:
            connection = yield gen.Task(self.pool.connection)
            response, error = yield gen.Task(self.database._command, ismaster,
                connection=connection)
        except InterfaceError, ie:
            logger.error('oops, database node {host}:{port} is unavailable: {error}' \
                .format(host=self.host, port=self.port, error=ie))

        if response:
            self.is_primary = response.get('ismaster', True)
            self.is_secondary = response.get('secondary', False)
            self.available = True
        else:
            self.available = False

        self.initialized = True

        if callback:
            callback()

    def disconnect(self):
        self.pool.close()

    def __repr__(self):
        return """MongoDB node {host}:{port} ({primary}, {secondary})""" \
            .format(host=self.host, port=self.port, primary=self.is_primary,
                secondary=self.is_secondary)


class ReadPreference(object):
    """Defines the read preferences supported by mongotor.

    * `PRIMARY`: Queries are sent to the primary of the replica set.
    * `PRIMARY_PREFERRED`: Queries are sent to the primary if available,
      otherwise a secondary.
    * `SECONDARY`: Queries are distributed among secondaries. An error
      is raised if no secondaries are available.
    * `SECONDARY_PREFERRED`: Queries are distributed among secondaries,
      or the primary if no secondary is available.
    * TODO: `NEAREST`: Queries are distributed among all members.
    """

    PRIMARY = 0
    PRIMARY_PREFERRED = 1
    SECONDARY = 2
    SECONDARY_ONLY = 2
    SECONDARY_PREFERRED = 3
    #NEAREST = 4

    @classmethod
    def select_primary_node(cls, nodes):
        for node in nodes:
            if node.available and node.is_primary:
                return node

    @classmethod
    def select_random_node(cls, nodes, secondary_only):
        candidates = []

        for node in nodes:
            if not node.available:
                continue

            if secondary_only and node.is_primary:
                continue

            candidates.append(node)

        if not candidates:
            return None

        return random.choice(candidates)

    @classmethod
    def select_node(cls, nodes, mode=None):
        if mode is None:
            mode = cls.PRIMARY

        if mode == cls.PRIMARY:
            return cls.select_primary_node(nodes)

        if mode == cls.PRIMARY_PREFERRED:
            primary_node = cls.select_primary_node(nodes)
            if primary_node:
                return primary_node
            else:
                return cls.select_node(nodes, cls.SECONDARY)

        if mode == cls.SECONDARY:
            return cls.select_random_node(nodes, secondary_only=True)

        if mode == cls.SECONDARY_PREFERRED:
            secondary_node = cls.select_random_node(nodes, secondary_only=True)
            if secondary_node:
                return secondary_node
            else:
                return cls.select_primary_node(nodes)
