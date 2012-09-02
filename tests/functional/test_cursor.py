# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from bson.objectid import ObjectId
from mongotor.cursor import Cursor
from mongotor.pool import ConnectionPool

import sure


class CursorTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        super(CursorTestCase, self).setUp()
        self.pool = ConnectionPool(["localhost:27017"], dbname='test')

    def tearDown(self):
        super(CursorTestCase, self).tearDown()
        self.pool.close()

    def test_can_be_insert_a_document(self):
        """[CursorTestCase] - Can be insert a document"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldBeName'}
        cursor.insert(document, callback=self.stop)

        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_can_be_insert_a_list_of_documents(self):
        """[CursorTestCase] - Can be insert a list of documents"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldBeName'},
            {'_id': ObjectId(), 'name': 'shouldBeName2'}]
        cursor.insert(documents, callback=self.stop)

        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none
