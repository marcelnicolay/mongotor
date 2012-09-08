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

from tornado import iostream, gen
from mongotor.errors import InterfaceError, IntegrityError
from mongotor import helpers
import socket
import logging
import struct

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, host, port, pool=None, autoreconnect=True, timeout=5):
        self._host = host
        self._port = port
        self._pool = pool
        self._autoreconnect = autoreconnect
        self._timeout = timeout
        self._connected = False

        self._connect()

    def _connect(self):

        try:
            socket.timeout(self._timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((self._host, self._port))

            self._stream = iostream.IOStream(s)
            self._stream.set_close_callback(self._close_stream)

            self._connected = True

        except socket.error, error:
            raise InterfaceError(error)

    def _parse_header(self, header, request_id):
        logging.debug('got data %r' % header)
        length = int(struct.unpack("<i", header[:4])[0])
        _request_id = struct.unpack("<i", header[8:12])[0]

        assert _request_id == request_id, \
            "ids don't match %r %r" % (request_id, _request_id)

        operation = 1 # who knows why
        assert operation == struct.unpack("<i", header[12:])[0]
        logging.debug('%s' % length)
        logging.debug('waiting for another %d bytes' % (length - 16))

        return length

    def _parse_response(self, response, request_id):
        try:
            response = helpers._unpack_response(response, request_id)
        except Exception, e:
            logger.error('error %s' % e)
            return None, e

        if response and response['data'] and response['data'][0].get('err') \
            and response['data'][0].get('code'):

            logger.error(response['data'][0]['err'])
            return response, IntegrityError(response['data'][0]['err'],
                code=response['data'][0]['code'])

        logger.info('response: %s' % response)
        return response, None

    def _close_stream(self):
        self._connected = False

    def close(self):
        self._connected = False
        self._stream.close()

        if self._pool:
            self._pool.release(self)

    def send_message(self, message, callback):
        if not self._connected:
            if self._autoreconnect:
                self._connect()
            else:
                raise InterfaceError('connection is closed and autoreconnect is false')

        self._send_message(message, callback)

    @gen.engine
    def _send_message(self, message, callback=None):
        (request_id, message) = message
        try:
            self._stream.write(message)

            header_data = yield gen.Task(self._stream.read_bytes, 16)
            length = self._parse_header(header_data, request_id)

            data = yield gen.Task(self._stream.read_bytes, length - 16)

            if self._pool:
                self._pool.release(self)

            response, error = self._parse_response(data, request_id)

            if callback:
                callback((response, error))

        except IOError, e:
            raise e
