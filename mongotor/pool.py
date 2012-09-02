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
      - `autoreconnnect`: autoreconnnect on database

    """
    def __init__(self, addresses, dbname, maxconnections=0,
        maxusage=0, autoreconnnect=True):

        assert isinstance(maxconnections, int)
        assert isinstance(maxusage, int)
        assert isinstance(dbname, (str, unicode))
        assert isinstance(autoreconnnect, bool)

        self._addresses = self._parse_addresses(addresses)
        self._maxconnections = maxconnections
        self._maxusage = maxusage
        self._autoreconnnect = autoreconnnect
        self._connections = 0
        self._idle_connections = []
        self._condition = Condition()

    def _parse_addresses(self, addresses):
        if isinstance(addresses, (str, unicode)):
            addresses = [addresses]

        assert isinstance(addresses, list)

        parsed_addresses = []
        for address in addresses:
            host, port = address.split(":")
            parsed_addresses.append((host, int(port)))

        return parsed_addresses

    def _create_connection(self):
        host, port = self._addresses[0]
        return Connection(self, host, port, self._autoreconnnect)

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
