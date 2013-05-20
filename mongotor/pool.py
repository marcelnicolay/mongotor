# coding: utf-8
# <mongotor - An asynchronous driver and toolkit for accessing MongoDB with Tornado>
# Copyright (C) <2012>  Marcel Nicolay <marcel.nicolay@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
from datetime import timedelta
from threading import Condition
from tornado.ioloop import IOLoop
from functools import partial
from mongotor.connection import Connection
from mongotor.errors import TooManyConnections

log = logging.getLogger(__name__)


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

        for i in range(self._maxconnections):
            conn = self._create_connection()
            self._idle_connections.append(conn)

    def __repr__(self):
        return "ConnectionPool {0}:{1}:{2} using:{3}, idle:{4} :::: "\
            .format(id(self), self._host, self._port, self._connections, len(self._idle_connections))

    def _create_connection(self):
        log.debug('{0} creating new connection'.format(self))
        return Connection(host=self._host, port=self._port, pool=self,
                          autoreconnect=self._autoreconnect)

    def connection(self, callback=None, retries=0):
        """Get a connection from pool

        :Parameters:
          - `callback` : method which will be called when connection is ready

        """
        self._condition.acquire()
        try:
            try:
                conn = self._idle_connections.pop(0)
            except IndexError:
                if self._maxconnections and self._connections >= self._maxconnections:
                    if retries > 10:
                        raise TooManyConnections()

                    log.warn('{0} too many connections, retries {1}'.format(self, retries))
                    retry_connection = partial(self.connection, retries=(retries + 1), callback=callback)
                    IOLoop.instance().add_timeout(timedelta(microseconds=300), retry_connection)

                    return

                conn = self._create_connection()

            self._connections += 1

        finally:
            self._condition.release()

        log.debug('{0} {1} connection retrieved'.format(self, conn))
        callback(conn)

    def release(self, conn):
        if self._maxusage and conn.usage > self._maxusage:
            if not conn.closed():
                log.debug('{0} {1} connection max usage expired, renewing...'.format(self, conn))
                self._connections -= 1
                conn.close()
            return

        self._condition.acquire()

        if conn in self._idle_connections:
            log.debug('{0} {1} called by socket close'.format(self, conn))
            self._condition.release()
            return

        try:
            self._idle_connections.append(conn)
            self._condition.notify()
        finally:
            self._connections -= 1
            self._condition.release()

        log.debug('{0} {1} release connection'.format(self, conn))

    def close(self):
        """Close all connections in the pool."""
        log.debug('{0} closing...'.format(self))
        self._condition.acquire()
        try:
            while self._idle_connections:  # close all idle connections
                con = self._idle_connections.pop(0)
                try:
                    con.close()
                except Exception:
                    pass
                self._connections -= 1
            self._condition.notifyAll()
        finally:
            self._condition.release()
