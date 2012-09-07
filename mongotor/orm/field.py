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

from datetime import datetime
from bson import ObjectId


class Field(object):

    def __init__(self, default=None, name=None, field_type=None):

        self.default = default
        self.field_type = field_type
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self

        value = instance._data.get(self.name)
        if value is None:
            return self.default

        return value

    def __set__(self, instance, value):

        if value is not None and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except TypeError:
                raise(TypeError("type of %s must be %s" % (self.name,
                    self.field_type)))
            except ValueError:
                raise(TypeError("type of %s must be %s" % (self.name,
                    self.field_type)))

        instance._data[self.name] = value


class StringField(Field):

    def __init__(self, *args, **kargs):
        super(StringField, self).__init__(field_type=unicode, *args, **kargs)


class IntegerField(Field):

    def __init__(self, *args, **kargs):
        super(IntegerField, self).__init__(field_type=int, *args, **kargs)


class DateTimeField(Field):

    def __init__(self, *args, **kargs):
        super(DateTimeField, self).__init__(field_type=datetime,
            *args, **kargs)


class BooleanField(Field):

    def __init__(self, *args, **kargs):
        super(BooleanField, self).__init__(field_type=bool, *args, **kargs)


class FloatField(Field):

    def __init__(self, *args, **kargs):
        super(FloatField, self).__init__(field_type=float, *args, **kargs)


class ListField(Field):

    def __init__(self, *args, **kargs):
        super(ListField, self).__init__(field_type=list, *args, **kargs)


class ObjectField(Field):

    def __init__(self, *args, **kargs):
        super(ObjectField, self).__init__(field_type=dict, *args, **kargs)


class ObjectIdField(Field):

    def __init__(self, *args, **kargs):
        super(ObjectIdField, self).__init__(field_type=ObjectId,
            *args, **kargs)
