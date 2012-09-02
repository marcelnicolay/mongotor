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
from mongotor.pool import ConnectionPool


class Database(object):
    """Database object
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls)

        return cls._instance

    def init(self, addresses, dbname, **kwargs):
        self._addresses = addresses
        self._dbname = dbname

        self._pool = ConnectionPool(addresses, dbname, **kwargs)

    def get_collection_name(self, collection):
        return u'%s.%s' % (self._dbname, collection)

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

        cls._instance._pool.close()
        cls._instance = None

    @gen.engine
    def send_message(self, message, callback=None):

        connection = yield gen.Task(self._pool.connection)
        try:
            connection.send_message(message, callback=callback)
        except:
            connection.close()
            raise

    @gen.engine
    def command(self, command, value=1, callback=None, check=True,
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

        from mongotor.cursor import Cursor
        cursor = Cursor('$cmd', command, is_command=True)
        cursor.find(limit=-1, callback=callback)
