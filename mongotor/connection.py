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
from tornado import iostream, gen
from mongotor.errors import InterfaceError, IntegrityError
from mongotor import helpers
import socket
import logging
import struct

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, pool, host, port, auto_reconnect=True):
        self._pool = pool
        self._host = host
        self._port = port
        self._auto_reconnect = auto_reconnect
        self._connected = False

        self._connect()

    def _connect(self):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((self._host, self._port))

            self._stream = iostream.IOStream(s)
            self._stream.set_close_callback(self._on_socket_close)

            self._connected = True

        except socket.error, error:
            raise InterfaceError(error)

    def _on_socket_close(self):
        self._connected = False

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

    def close(self):
        self._connected = False
        self._stream.close()
        self._pool.release(self)

    def send_message(self, message, callback):
        if not self._connected:
            if self._auto_reconnect:
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

            self._pool.release(self)

            response, error = self._parse_response(data, request_id)

            if callback:
                callback((response, error))

        except IOError, e:
            raise e

