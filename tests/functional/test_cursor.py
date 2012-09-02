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

    def test_insert_a_document(self):
        """[CursorTestCase] - insert a document"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldBeName'}
        cursor.insert(document, callback=self.stop)

        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_insert_a_list_of_documents(self):
        """[CursorTestCase] - insert a list of documents"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldBeName'},
            {'_id': ObjectId(), 'name': 'shouldBeName2'}]
        cursor.insert(documents, callback=self.stop)

        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_remove_a_document_by_id(self):
        """[CursorTestCase] - remove a document by id"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldBeName'}
        cursor.insert(document, callback=self.stop)
        response, error = self.wait()

        cursor.remove(document['_id'], callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_remove_all_documents(self):
        """[CursorTestCase] - remove all documents"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        cursor.remove(None, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_update_a_document(self):
        """[CursorTestCase] - update a document"""

        cursor = Cursor(pool=self.pool, collection='test', dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldBeName'}
        cursor.insert(document, callback=self.stop)
        response, error = self.wait()

        cursor.update({'_id': document['_id']}, {'$set': \
            {'name': 'shouldBeUpdateName'}}, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        response['data'][0]['updatedExisting'].should.be.ok
        error.should.be.none
