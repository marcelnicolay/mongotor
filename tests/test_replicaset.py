# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from mongotor.node import ReadPreference
import sure
import os
import time


class ReplicaSetTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(ReplicaSetTestCase, self).tearDown()
        Database._instance = None

    def test_configure_nodes(self):
        """[ReplicaSetTestCase] - Configure nodes"""

        Database.connect(["localhost:27027", "localhost:27028"], dbname='test')

        master_node = ReadPreference.select_primary_node(Database()._nodes)
        secondary_node = ReadPreference.select_node(Database()._nodes, mode=ReadPreference.SECONDARY)

        master_node.host.should.be('localhost')
        master_node.port.should.be(27027)

        secondary_node.host.should.be('localhost')
        secondary_node.port.should.be(27028)

        nodes = Database()._nodes
        nodes.should.have.length_of(2)
