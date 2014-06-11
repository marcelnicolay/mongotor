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
from __future__ import with_statement
from tornado import iostream
from tornado import stack_context
from mongotor.errors import InterfaceError, IntegrityError, \
    ProgrammingError, DatabaseError
from mongotor import helpers
import socket
import logging
import struct
import contextlib

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, host, port, pool=None, autoreconnect=True, timeout=5):
        self._host = host
        self._port = port
        self._pool = pool
        self._autoreconnect = autoreconnect
        self._timeout = timeout
        self._connected = False
        self._callback = None

        self._connect()

        logger.debug('{0} created'.format(self))

    def _connect(self):
        self.usage = 0
        try:
            socket.timeout(self._timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((self._host, self._port))

            self._stream = iostream.IOStream(s)
            self._stream.set_close_callback(self._socket_close)

            self._connected = True
        except socket.error, error:
            raise InterfaceError(error)

    def __repr__(self):
        return "Connection {0} ::: ".format(id(self))

    def _parse_header(self, header):
        #logger.debug('got data %r' % header)
        length = int(struct.unpack("<i", header[:4])[0])
        _request_id = struct.unpack("<i", header[8:12])[0]

        assert _request_id == self._request_id, \
            "ids don't match %r %r" % (self._request_id, _request_id)

        operation = 1  # who knows why
        assert operation == struct.unpack("<i", header[12:])[0]
        #logger.debug('%s' % length)
        #logger.debug('waiting for another %d bytes' % (length - 16))

        self._stream.read_bytes(length - 16, callback=self._parse_response)

    def _parse_response(self, response):
        callback = self._callback
        check_response = self._check_response
        self.reset()
        self.release()

        if check_response:
            response = self.__check_response_to_last_error(response)

        #logger.debug('response: %s' % response)
        callback((response, None))

    def __check_response_to_last_error(self, response):
        """Check a response to a lastError message for errors.

        `response` is a byte string representing a response to the message.
        If it represents an error response we raise DatabaseError.

        Return the response as a document.
        """
        response = helpers._unpack_response(response)
        assert response["number_returned"] == 1
        error = response["data"][0]

        helpers._check_command_response(error)

        error_msg = error.get("err", "")
        if error_msg is None:
            return error

        details = error
        # mongos returns the error code in an error object
        # for some errors.
        if "errObjects" in error:
            for errobj in error["errObjects"]:
                if errobj["err"] == error_msg:
                    details = errobj
                    break

        if "code" in details:
            if details["code"] in [11000, 11001, 12582]:
                raise IntegrityError(details["err"])
            else:
                raise DatabaseError(details["err"], details["code"])
        else:
            raise DatabaseError(details["err"])

    def _socket_close(self):
        logger.debug('{0} connection stream closed'.format(self))
        if self._callback:
            self._callback((None, InterfaceError('connection closed')))

        self.reset()
        self._connected = False
        self.release()

    def close(self):
        logger.debug('{0} connection close'.format(self))
        if self._callback:
            self._callback((None, InterfaceError('connection closed')))

        self.reset()
        self._connected = False
        self._stream.close()

    def closed(self):
        return not self._connected

    def release(self):
        if self._pool:
            self._pool.release(self)

    def reset(self):
        self._callback = None
        self._request_id = None
        self._check_response = False

    @contextlib.contextmanager
    def close_on_error(self):
        try:
            yield
        except DatabaseError, de:
            logger.error('database error'.format(de))
            raise
        except Exception:
            logger.error('{0} exception in operation'.format(self))
            self.close()
            raise

    def send_message(self, message, with_last_error=False, callback=None):
        """Say something to Mongo.

        Raises ConnectionFailure if the message cannot be sent. Raises
        OperationFailure if `with_last_error` is ``True`` and the
        response to the getLastError call returns an error. Return the
        response from lastError, or ``None`` if `with_last_error`
        is ``False``.

        :Parameters:
          - `message`: message to send
          - `with_last_error`: check getLastError status after sending the
            message
        """
        if self._callback is not None:
            raise ProgrammingError('connection already in use')

        if self.closed():
            if self._autoreconnect:
                self._connect()
            else:
                raise InterfaceError('connection is closed and autoreconnect is false')

        self._callback = stack_context.wrap(callback)
        self._check_response = with_last_error

        with stack_context.StackContext(self.close_on_error):
            self.__send_message(message, with_last_error=with_last_error)

    def __send_message(self, message, with_last_error=False):
        self.usage += 1

        (self._request_id, message) = message

        self._stream.write(message)

        if with_last_error:
            self._stream.read_bytes(16, callback=self._parse_header)
            return

        self.reset()
        self.release()

        if self._callback:
            self._callback()

    def send_message_with_response(self, message, callback):
        """Send a message to Mongo and return the response.

        Sends the given message and returns the response.

        :Parameters:
          - `message`: (request_id, data) pair making up the message to send
        """
        if self._callback is not None:
            raise ProgrammingError('connection already in use')

        if self.closed():
            if self._autoreconnect:
                self._connect()
            else:
                raise InterfaceError('connection is closed and autoreconnect is false')

        self._callback = stack_context.wrap(callback)
        self._check_response = False

        with stack_context.StackContext(self.close_on_error):
            self.__send_message_and_receive(message)

    def __send_message_and_receive(self, message):
        self.usage += 1

        (self._request_id, message) = message

        self._stream.write(message)
        self._stream.read_bytes(16, callback=self._parse_header)
