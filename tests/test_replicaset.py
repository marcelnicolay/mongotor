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

    def test_configure_nodes_when_one_node_is_unavailable(self):
        """[ReplicaSetTestCase] - Configure nodes when one node is unavailable"""

        os.system('make mongo-kill > /dev/null 2>&1')
        os.system('make mongo-start-node1 > /dev/null 2>&1')
        os.system('make mongo-start-arbiter > /dev/null 2>&1')

        # wait for the node1 turn master
        time.sleep(10)

        Database.connect(["localhost:27027", "localhost:27028"], dbname='test')

        master_node = ReadPreference.select_primary_node(Database()._nodes)

        master_node.host.should.be('localhost')
        master_node.port.should.be(27027)

        nodes = Database()._nodes
        nodes.should.have.length_of(2)

        for node in nodes:
            if node.port == 27028:
                node.available.shouldnot.be.ok

        os.system('make mongo-start > /dev/null 2>&1')
