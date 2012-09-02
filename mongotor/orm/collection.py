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
import logging
from tornado import gen
from mongotor import message
from mongotor.orm.field import Field
from mongotor.orm.signal import (pre_save, post_save,
    pre_remove, post_remove, pre_update, post_update)
from mongotor.orm.manager import Manager
from mongotor.database import Database


logger = logging.getLogger(__name__)
__lazy_classes__ = {}


class CollectionMetaClass(type):

    def __new__(cls, name, bases, attrs):
        global __lazy_classes__

        # Add the document's fields to the _data
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, "__class__") and\
                issubclass(attr_value.__class__, Field):

                attr_value.name = attr_name

        new_class = super(CollectionMetaClass, cls).__new__(cls, name,
            bases, attrs)

        __lazy_classes__[name] = new_class

        new_class.objects = Manager(collection=new_class)

        return new_class


class Collection(object):
    """Collection class
    """
    __metaclass__ = CollectionMetaClass

    def __new__(cls, class_name=None, *args, **kwargs):
        if class_name:
            global __lazy_classes__
            return __lazy_classes__.get(class_name)

        return super(Collection, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        self._data = {}

    def as_dict(self):
        items = {}
        for attr_name, attr_type in self.__class__.__dict__.iteritems():
            if isinstance(attr_type, Field):
                attr_value = getattr(self, attr_name)
                if attr_value != None:
                    items[attr_name] = attr_value
        return items

    @classmethod
    def create(cls, dictionary):
        instance = cls()
        for (key, value) in dictionary.items():
            try:
                setattr(instance, str(key), value)
            except TypeError, e:
                logger.warn(e)

        return instance

    @gen.engine
    def save(self, safe=True, callback=None):
        """Save a document

        :Parameters:
        - `safe` (optional): safe insert operation 
        - `callback` : method which will be called when save is finished
        """
        pre_save.send(instance=self)

        database = Database()
        collection_name = database.get_collection_name(self.__collection__)

        message_insert = message.insert(collection_name, [self.as_dict()],
            True, safe, {})

        response, error = yield gen.Task(database.send_message, message_insert)

        post_save.send(instance=self)

        if callback:
            callback((response, error))

    @gen.engine
    def remove(self, safe=True, callback=None):
        """Remove a document

        :Parameters:
        - `safe` (optional): safe remove operation
        - `callback` : method which will be called when remove is finished
        """
        pre_remove.send(instance=self)

        database = Database()
        collection_name = database.get_collection_name(self.__collection__)

        message_delete = message.delete(collection_name, {'_id': self._id},
            safe, {})

        response, error = yield gen.Task(database.send_message, message_delete)

        post_remove.send(instance=self)

        if callback:
            callback((response, error))

    @gen.engine
    def update(self, document=None, safe=True, callback=None):
        """Update a document

        :Parameters:
        - `safe` (optional): safe update operation
        - `callback` : method which will be called when update is finished
        """
        pre_update.send(instance=self)

        if not document:
            document = self.as_dict()

        database = Database()
        collection_name = database.get_collection_name(self.__collection__)
        spec = {'_id': self._id}

        message_update = message.update(collection_name, False,
                False, spec, document, safe, {})

        response, error = yield gen.Task(database.send_message, message_update)

        post_update.send(instance=self)

        if callback:
            callback((response, error))
