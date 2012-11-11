# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from bson import ObjectId
import sure


class ClientTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(ClientTestCase, self).tearDown()
        Database().collection_test.remove({})
        Database._instance = None

    def test_insert_a_single_document(self):
        """[ClientTestCase] - insert a single document with client"""

        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldbename'}

        db.collection_test.insert(document, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_insert_a_document_list(self):
        """[ClientTestCase] - insert a list of document with client"""

        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_remove_document_by_id(self):
        """[ClientTestCase] - remove a document by id"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.remove(documents[0]['_id'], callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_remove_document_by_spec(self):
        """[ClientTestCase] - remove a document by spec"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.remove({'name': 'shouldbename'}, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_update_document(self):
        """[ClientTestCase] - update a document"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.update(documents[0], {'$set': {'name':
            'should be a new name'}}, callback=self.stop)
        response, error = self.wait()

        response['data'][0]['ok'].should.be.equal(1.0)
        error.should.be.none

    def test_find_document(self):
        """[ClientTestCase] - find a document"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'someflag': 1},
            {'_id': ObjectId(), 'someflag': 1},
            {'_id': ObjectId(), 'someflag': 2}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({'someflag': 1}, callback=self.stop)
        response, error = self.wait()

        response[0]['_id'].should.be(documents[0]['_id'])
        response[1]['_id'].should.be(documents[1]['_id'])
        error.should.be.none

    def test_find_one_document(self):
        """[ClientTestCase] - find one document"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find_one({'param': 'shouldbeparam1'},
            callback=self.stop)
        response, error = self.wait()

        response['_id'].should.be(documents[1]['_id'])
        error.should.be.none

    def test_find_one_document_by_id(self):
        """[ClientTestCase] - find one document by id"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find_one(documents[2]['_id'],
            callback=self.stop)
        response, error = self.wait()

        response['_id'].should.be(documents[2]['_id'])
        error.should.be.none

    def test_count_documents_in_find(self):
        """[ClientTestCase] - counting documents"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({"param": 'shouldbeparam1'}).count(callback=self.stop)
        total = self.wait()

        total.should.be.equal(2)

    def test_distinct_documents_in_find(self):
        """[ClientTestCase] - distinct documents"""
        db = Database.connect(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam2', 'uuid': 200}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({"param": 'shouldbeparam1'}).distinct('uuid', callback=self.stop)
        distincts = self.wait()

        distincts.should.have.length_of(1)
        distincts[0].should.be.equal(100)
