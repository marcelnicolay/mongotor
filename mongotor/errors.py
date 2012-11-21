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


class Error(StandardError):
    """Base class for all mongotor exceptions.

    """


class InterfaceError(Error):
    """Raised when a connection to the database cannot be made or is lost.
    """


class TooManyConnections(InterfaceError):
    """Raised when a pool is busy.
    """


class InvalidOperationError(Error):
    """Raised when a client attempts to perform an invalid operation.
    """


class DatabaseError(Error):
    """Raised when a database operation fails.

    """

    def __init__(self, error, code=None):
        self.code = code
        Error.__init__(self, error)


class IntegrityError(DatabaseError):
    """Raised when a safe insert or update fails due to a duplicate key error.

    """
    def __init__(self, msg, code=None):
        self.code = code
        self.msg = msg


class ProgrammingError(DatabaseError):
    pass


class TimeoutError(DatabaseError):
    """Raised when a database operation times out.
    """
