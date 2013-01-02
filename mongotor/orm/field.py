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

import uuid
import re
import decimal
from datetime import datetime
from bson import ObjectId


class Field(object):

    def __init__(self, default=None, name=None, field_type=None):

        self.field_type = field_type
        self.name = name
        self.default = self._validate(default)

    def __get__(self, instance, owner):
        if not instance:
            return self

        value = instance._data.get(self.name)
        if value is None:
            return self.default() if callable(self.default) else self.default

        return value

    def __set__(self, instance, value):
        value = self._validate(value)
        if self.name not in instance._data or instance._data[self.name] != value:
            instance._dirty.add(self.name)
        instance._data[self.name] = value

    def _validate(self, value):
        if value is not None and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except TypeError:
                raise(TypeError("type of %s must be %s" % (self.name,
                                                           self.field_type)))
            except ValueError:
                raise(TypeError("type of %s must be %s" % (self.name,
                                                           self.field_type)))
        return value


class StringField(Field):

    def __init__(self, regex=None, *args, **kwargs):
        self.regex = re.compile(regex) if regex else None
        super(StringField, self).__init__(field_type=unicode, *args, **kwargs)

    def _validate(self, value):
        value = super(StringField, self)._validate(value)
        if self.regex is not None and self.regex.match(value) is None:
            raise(TypeError("Value did not match regex"))

        return value


class UrlField(StringField):

    REGEX = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super(UrlField, self).__init__(self.REGEX, *args, **kwargs)


class EmailField(StringField):

    REGEX = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016'
        r'-\177])*"'
        # domain
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super(EmailField, self).__init__(self.REGEX, *args, **kwargs)


class NumberField(Field):

    def __init__(self, field_type, min_value=None, max_value=None,
                 *args, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super(NumberField, self).__init__(field_type=field_type,
            *args, **kwargs)

    def _validate(self, value):
        value = super(NumberField, self)._validate(value)
        if self.min_value is not None and value < self.min_value:
            raise(TypeError("Value can not be less than %s" % (self.min_value)))

        if self.max_value is not None and value > self.max_value:
            raise(TypeError("Value can not be more than %s" & (self.max_value)))

        return value


class IntegerField(NumberField):

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(int, *args, **kwargs)


class LongField(NumberField):

    def __init__(self, *args, **kwargs):
        super(LongField, self).__init__(long, *args, **kwargs)


class FloatField(NumberField):

    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__(float, *args, **kwargs)


class DecimalField(NumberField):

    def __init__(self, *args, **kwargs):
        super(DecimalField, self).__init__(decimal.Decimal, *args, **kwargs)


class DateTimeField(Field):

    def __init__(self, *args, **kwargs):
        super(DateTimeField, self).__init__(field_type=datetime,
            *args, **kwargs)


class BooleanField(Field):

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(field_type=bool, *args, **kwargs)


class ListField(Field):

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(field_type=list, *args, **kwargs)


class ObjectField(Field):

    def __init__(self, *args, **kwargs):
        super(ObjectField, self).__init__(field_type=dict, *args, **kwargs)


class ObjectIdField(Field):

    def __init__(self, *args, **kwargs):
        super(ObjectIdField, self).__init__(field_type=ObjectId,
            *args, **kwargs)


class UuidField(Field):

    def __init__(self, *args, **kwargs):
        super(UuidField, self).__init__(field_type=uuid.UUID, *args, **kwargs)


class Md5Field(Field):

    length = 32

    def __init__(self, *args, **kwargs):
        super(Md5Field, self).__init__(field_type=unicode, *args, **kwargs)

    def _validate(self, value):
        value = super(Md5Field, self)._validate(value)
        if len(value) is not self.length:
            raise(TypeError("Md5 dose not have the correct length"))

        try:
            int(value, 16)
        except:
            raise(TypeError("The Md5 hash should be a 16byte hash value"))

        return value


class Sha1Field(Field):

    length = 40

    def __init__(self, *args, **kwargs):
        super(Sha1Field, self).__init__(field_type=unicode, *args, **kwargs)

    def _validate(self, value):
        value = super(Sha1Field, self)._validate(value)
        if len(value) is not self.length:
            raise(TypeError("Sha1 dose not have the correct length"))

        try:
            int(value, 20)
        except:
            raise(TypeError("The Sha1 hash should be a 20byte hash value"))

        return  value
