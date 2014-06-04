# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from bson import ObjectId
from mongotor.errors import DatabaseError
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
        Database.disconnect()

    def test_configure_nodes(self):
        """[ReplicaSetTestCase] - Configure nodes"""

        db = Database.init(["localhost:27027", "localhost:27028"], dbname='test')
        db._connect(callback=self.stop)
        self.wait()

        master_node = ReadPreference.select_primary_node(Database()._nodes)
        secondary_node = ReadPreference.select_node(Database()._nodes, mode=ReadPreference.SECONDARY)

        master_node.host.should.be('localhost')
        master_node.port.should.be(27027)

        secondary_node.host.should.be('localhost')
        secondary_node.port.should.be(27028)

        nodes = Database()._nodes
        nodes.should.have.length_of(2)

    def test_raises_error_when_mode_is_secondary_and_secondary_is_down(self):
        """[ReplicaSetTestCase] - Raise error when mode is secondary and secondary is down"""
        os.system('make mongo-kill-node2')
        time.sleep(1)  # stops are fast

        try:
            db = Database.init(["localhost:27027", "localhost:27028"], dbname='test')
            db._connect(callback=self.stop)
            self.wait()

            Database().send_message.when.called_with((None, ''),
                read_preference=ReadPreference.SECONDARY)\
                .throw(DatabaseError)
        finally:
            os.system('make mongo-start-node2')
            time.sleep(5)  # wait to become secondary again


class SecondaryPreferredTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(SecondaryPreferredTestCase, self).tearDown()
        Database._instance = None

    def test_find_on_secondary(self):
        """[SecondaryPreferredTestCase] - test find document from secondary"""
        db = Database.init(["localhost:27027", "localhost:27028"], dbname='test',
            read_preference=ReadPreference.SECONDARY_PREFERRED)
        db._connect(callback=self.stop)
        self.wait()

        doc = {'_id': ObjectId()}
        db.test.insert(doc, callback=self.stop)
        self.wait()

        time.sleep(2)
        db.test.find_one(doc, callback=self.stop)
        doc_found, error = self.wait()

        doc_found.should.be.eql(doc)
