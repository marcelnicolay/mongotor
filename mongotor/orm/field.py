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
