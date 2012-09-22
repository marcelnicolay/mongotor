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

from functools import partial, wraps
from datetime import timedelta
from tornado import gen
from tornado.ioloop import IOLoop
from bson import SON
from mongotor.node import Node, ReadPreference
from mongotor.errors import DatabaseError
from mongotor.client import Client


def connected(fn):
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        if not hasattr(self, '_initialized'):
            raise DatabaseError("you must be connect to database before perform this action")

        return fn(self, *args, **kwargs)

    return wrapped


class Database(object):
    """Database object
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls)

        return cls._instance

    def init(self, addresses, dbname, read_preference=None, **kwargs):
        self._addresses = self._parse_addresses(addresses)
        self._dbname = dbname
        self._read_preference = read_preference or ReadPreference.PRIMARY
        self._nodes = []
        self._pool_kwargs = kwargs
        self._initialized = False

        for host, port in self._addresses:
            node = Node(host, port, self, self._pool_kwargs)
            self._nodes.append(node)

        ioloop_is_running = IOLoop.instance().running()
        self._config_nodes(callback=partial(self._on_config_node, ioloop_is_running))

        while True:
            if not ioloop_is_running:
                IOLoop.instance().start()

            if self._initialized:
                break

        IOLoop.instance().add_timeout(timedelta(seconds=5), self._config_nodes)

    def _on_config_node(self, ioloop_is_running):
        for node in self._nodes:
            if not node.initialized:
                return

        self._initialized = True
        if not ioloop_is_running:
            IOLoop.instance().stop()

    @property
    def dbname(self):
        return self._dbname

    @connected
    def get_collection_name(self, collection):
        return u'%s.%s' % (self.dbname, collection)

    def _parse_addresses(self, addresses):
        if isinstance(addresses, (str, unicode)):
            addresses = [addresses]

        assert isinstance(addresses, list)

        parsed_addresses = []
        for address in addresses:
            host, port = address.split(":")
            parsed_addresses.append((host, int(port)))

        return parsed_addresses

    def _config_nodes(self, callback=None):

        for node in self._nodes:
            node.config(callback)

    @classmethod
    def connect(cls, addresses, dbname, read_preference=None, **kwargs):
        """Connect to database

        >>> Database.connect(['localhost:27017', 'localhost:27018'], 'test', maxconnections=100)
        >>> db = Database()
        >>> db.collection.insert({...}, callback=...)

        :Parameters:
          - `addresses` : addresses can be a list or a simple string, host:port
          - `dbname` : mongo database name
          - `read_preference` (optional): The read preference for
            this query.
          - `maxconnections` (optional): maximum open connections for pool. 0 for unlimited
          - `maxusage` (optional): number of requests allowed on a connection
            before it is closed. 0 for unlimited
          - `autoreconnect`: autoreconnect to database. default is True
        """
        if cls._instance and hasattr(cls._instance, '_initialized'):
            return cls._instance

        database = Database()
        database.init(addresses, dbname, read_preference, **kwargs)

        return database

    @classmethod
    def disconnect(cls):
        """Disconnect to database

        >>> Database.disconnect()

        """
        if not cls._instance or not hasattr(cls._instance, '_initialized'):
            raise ValueError("Database isn't connected")

        for node in cls._instance._nodes:
            node.disconnect()

        cls._instance = None

    @gen.engine
    @connected
    def send_message(self, message, read_preference=None, callback=None):
        if read_preference is None:
            read_preference = self._read_preference

        node = ReadPreference.select_node(self._nodes, read_preference)
        if not node:
            raise DatabaseError('could not find an available node')

        connection = yield gen.Task(node.pool.connection)
        try:
            connection.send_message(message, callback=callback)
        except:
            connection.close()
            raise

    @connected
    def command(self, command, value=1, read_preference=None,
        callback=None, check=True, allowable_errors=[], **kwargs):
        """Issue a MongoDB command.

        Send command `command` to the database and return the
        response. If `command` is an instance of :class:`basestring`
        then the command {`command`: `value`} will be sent. Otherwise,
        `command` must be an instance of :class:`dict` and will be
        sent as is.

        Any additional keyword arguments will be added to the final
        command document before it is sent.

        For example, a command like ``{buildinfo: 1}`` can be sent
        using:

        >>> db.command("buildinfo")

        For a command where the value matters, like ``{collstats:
        collection_name}`` we can do:

        >>> db.command("collstats", collection_name)

        For commands that take additional arguments we can use
        kwargs. So ``{filemd5: object_id, root: file_root}`` becomes:

        >>> db.command("filemd5", object_id, root=file_root)

        :Parameters:
          - `command`: document representing the command to be issued,
            or the name of the command (for simple commands only).

            .. note:: the order of keys in the `command` document is
               significant (the "verb" must come first), so commands
               which require multiple keys (e.g. `findandmodify`)
               should use an instance of :class:`~bson.son.SON` or
               a string and kwargs instead of a Python `dict`.

          - `value` (optional): value to use for the command verb when
            `command` is passed as a string
          - `**kwargs` (optional): additional keyword arguments will
            be added to the command document before it is sent

        """
        if isinstance(command, basestring):
            command = SON([(command, value)])

        command.update(kwargs)

        if read_preference is None:
            read_preference = self._read_preference

        self._command(command, read_preference=read_preference, callback=callback)

    def _command(self, command, read_preference=None,
        connection=None, callback=None):

        if read_preference is None:
            read_preference = self._read_preference

        client = Client(self, '$cmd')

        client.find_one(command, is_command=True, connection=connection,
            read_preference=read_preference, callback=callback)

    def __getattr__(self, name):
        """Get a client collection by name.

        :Parameters:
          - `name`: the name of the collection
        """
        return Client(self, name)
