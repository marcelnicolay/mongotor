# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from mongotor.orm.collection import Collection
from mongotor.orm.field import ObjectIdField, StringField
from bson.objectid import ObjectId
import sure


class CollectionTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        super(CollectionTestCase, self).setUp()
        Database.connect(["localhost:27017"], dbname='test')

    def tearDown(self):
        super(CollectionTestCase, self).tearDown()
        Database.disconnect()

    def test_save_a_new_document(self):
        """[CollectionTestCase] - Save a new document using collection schema"""
        class CollectionTest(Collection):
            __collection__ = "collection_test"
            _id = ObjectIdField()
            string_attr = StringField()

        doc_test = CollectionTest()
        doc_test._id = ObjectId()
        doc_test.string_attr = "should be string value"

        doc_test.save(callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_remove_a_document(self):
        """[CollectionTestCase] - Remove a document"""
        class CollectionTest(Collection):
            __collection__ = "collection_test"
            _id = ObjectIdField()
            string_attr = StringField()

        doc_test = CollectionTest()
        doc_test._id = ObjectId()
        doc_test.string_attr = "should be string value"

        doc_test.save(callback=self.stop)
        self.wait()

        doc_test.remove(callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_update_a_document(self):
        """[CollectionTestCase] - Update a document"""
        class CollectionTest(Collection):
            __collection__ = "collection_test"
            _id = ObjectIdField()
            string_attr = StringField()

        doc_test = CollectionTest()
        doc_test._id = ObjectId()
        doc_test.string_attr = "should be string value"

        doc_test.save(callback=self.stop)
        self.wait()

        doc_test.string_attr = "should be new string value"
        doc_test.update(callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none
