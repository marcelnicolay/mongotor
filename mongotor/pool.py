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

from threading import Condition
from tornado.ioloop import IOLoop
from functools import partial
from mongotor.connection import Connection


class ConnectionPool(object):
    """Connection Pool

    :Parameters:
      - `maxconnections` (optional): maximum open connections for this pool. 0 for unlimited
      - `maxusage` (optional): number of requests allowed on a connection before it is closed. 0 for unlimited
      - `dbname`: mongo database name
      - `autoreconnect`: autoreconnect on database

    """
    def __init__(self, host, port, dbname, maxconnections=0, maxusage=0,
        autoreconnect=True):

        assert isinstance(host, (str, unicode))
        assert isinstance(port, int)
        assert isinstance(maxconnections, int)
        assert isinstance(maxusage, int)
        assert isinstance(dbname, (str, unicode))
        assert isinstance(autoreconnect, bool)

        self._host = host
        self._port = port
        self._maxconnections = maxconnections
        self._maxusage = maxusage
        self._autoreconnect = autoreconnect
        self._connections = 0
        self._idle_connections = []
        self._condition = Condition()

    def _create_connection(self):
        return Connection(host=self._host, port=self._port, pool=self,
            autoreconnect=self._autoreconnect)

    def connection(self, callback):
        """Get a connection from pool

        :Parameters:
          - `callback` : method which will be called when connection is ready

        """
        self._condition.acquire()

        try:
            conn = self._idle_connections.pop(0)

        except IndexError:
            if self._maxconnections and \
                self._connections >= self._maxconnections:

                retry_connection = partial(self.connection, callback)
                IOLoop.instance().add_callback(retry_connection)

                return

            conn = self._create_connection()
            self._connections += 1

        finally:
            self._condition.release()

        return callback(conn)

    def release(self, conn):
        self._condition.acquire()
        try:
            self._idle_connections.append(conn)
        finally:
            self._condition.release()

    def close(self):
        """Close all connections in the pool."""
        self._condition.acquire()
        try:
            while self._idle_connections:  # close all idle connections
                con = self._idle_connections.pop(0)
                try:
                    con._close()
                except Exception:
                    pass
                self._connections -= 1
            self._condition.notifyAll()
        finally:
            self._condition.release()
