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


class Signal(object):

    def __init__(self):
        self.receivers = []

    def connect(self, sender, handler):
        self.receivers.append((sender, handler))

    def disconnect(self, sender, handler):
        self.receivers.remove((sender, handler))

    def send(self, instance):
        for sender, handler in self.receivers:
            if isinstance(instance, sender):
                handler(sender, instance)


def receiver(signal, sender):

    def _decorator(handler):
        signal.connect(sender, handler)
        return handler

    return _decorator

pre_save = Signal()
post_save = Signal()

pre_remove = Signal()
post_remove = Signal()

pre_update = Signal()
post_update = Signal()
