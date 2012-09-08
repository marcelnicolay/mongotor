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
from functools import partial
from tornado import gen
from tornado.ioloop import IOLoop
from bson import SON
from mongotor.pool import ConnectionPool
from mongotor.connection import Connection
from mongotor.errors import InterfaceError

logger = logging.getLogger(__name__)


class Seed(object):
    """Seed is a node of database cluster
    """

    def __init__(self, host, port, dbname, pool_kargs=None):
        if not pool_kargs:
            pool_kargs = {}

        assert isinstance(host, (str, unicode))
        assert isinstance(dbname, (str, unicode))
        assert isinstance(port, int)

        self.host = host
        self.port = port
        self.dbname = dbname
        self.pool_kargs = pool_kargs

        self.is_master = False
        self.available = False

        self.pool = ConnectionPool(self.host, self.port, self.dbname, **self.pool_kargs)

    @gen.engine
    def config(self, callback):
        conn = Connection(self.host, self.port)
        ismaster = SON([('ismaster', 1)])

        response = None
        try:
            response, error = yield gen.Task(Database()._command, ismaster,
                connection=conn)
        except InterfaceError, ie:
            logger.error('oops, database seed {host}:{port} is unavailable: {error}' \
                .format(host=self.host, port=self.port, error=ie))
        finally:
            conn.close()

        if response:
            self.is_master = response['ismaster']
            self.available = True
            callback()
        else:
            self.available = False
            callback()

    def disconnect(self):
        self.pool.close()


class Database(object):
    """Database object
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls)

        return cls._instance

    def init(self, addresses, dbname, **kwargs):
        self._addresses = self._parse_addresses(addresses)
        self._dbname = dbname
        self._connected = False
        self._seeds = []
        self._pool_kwargs = kwargs

        self._config_seeds()

    def get_collection_name(self, collection):
        return u'%s.%s' % (self._dbname, collection)

    def _parse_addresses(self, addresses):
        if isinstance(addresses, (str, unicode)):
            addresses = [addresses]

        assert isinstance(addresses, list)

        parsed_addresses = []
        for address in addresses:
            host, port = address.split(":")
            parsed_addresses.append((host, int(port)))

        return parsed_addresses

    @gen.engine
    def _config_seeds(self):

        if not self._seeds:
            for host, port in self._addresses:
                seed = Seed(host, port, self._dbname, self._pool_kwargs)
                self._seeds.append(seed)

        for seed in self._seeds:
            yield gen.Task(seed.config)

    def _get_master_seed(self, callback):
        for seed in self._seeds:
            if seed.available and seed.is_master:
                callback(seed)
                return

        # wait for a master and avaiable seed
        IOLoop.instance().add_callback(partial(self._get_master_seed, callback))

    def _get_slave_seed(self, callback):

        for seed in self._seeds:
            if seed.available and not seed.is_master:
                callback(seed)
                return

        # slave seed not found, getting master seed
        self._get_master_seed(callback=callback)

    @gen.engine
    def get_connection(self, is_master=False, callback=None):
        if not is_master:
            seed = yield gen.Task(self._get_slave_seed)
        else:
            seed = yield gen.Task(self._get_master_seed)

        connection = yield gen.Task(seed.pool.connection)
        callback(connection)

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

        for seed in cls._instance._seeds:
            seed.disconnect()

        cls._instance = None

    @gen.engine
    def send_message(self, message, is_master=False, callback=None):

        connection = yield gen.Task(self.get_connection, is_master)
        try:
            connection.send_message(message, callback=callback)
        except:
            connection.close()
            raise

    def command(self, command, value=1, is_master=True, callback=None, check=True,
        allowable_errors=[], **kwargs):
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

        .. mongodoc:: commands
        """
        if isinstance(command, basestring):
            command = SON([(command, value)])

        command.update(kwargs)
        self._command(command, is_master=True, callback=callback)

    def _command(self, command, is_master=True, connection=None, callback=None):
        from mongotor.cursor import Cursor

        cursor = Cursor('$cmd', command, is_command=True, is_master=is_master, connection=connection)
        cursor.find(limit=-1, callback=callback)
