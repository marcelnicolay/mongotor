# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from bson.objectid import ObjectId
from mongotor import message
from mongotor.cursor import Cursor, DESCENDING, ASCENDING
from mongotor.database import Database
from mongotor.node import ReadPreference
import sure


class CursorTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        super(CursorTestCase, self).setUp()
        Database.init(["localhost:27027", "localhost:27028"], dbname='mongotor_test')

    def tearDown(self):
        super(CursorTestCase, self).tearDown()

        # delete all documents
        message_delete = message.delete('mongotor_test.cursor_test',
            {}, True, {})

        Database().get_node(ReadPreference.PRIMARY, callback=self.stop)
        node = self.wait()
        node.connection(self.stop)
        connection = self.wait()

        connection.send_message(message_delete, with_last_error=True, callback=self.stop)
        self.wait()

        Database.disconnect()

    def _insert_document(self, document):
        message_insert = message.insert('mongotor_test.cursor_test', [document],
            True, True, {})

        Database().get_node(ReadPreference.PRIMARY, callback=self.stop)
        node = self.wait()
        node.connection(self.stop)
        connection = self.wait()

        connection.send_message(message_insert, with_last_error=True, callback=self.stop)
        self.wait()

    def test_find_document_whitout_spec(self):
        """[CursorTestCase] - Find one document without spec"""

        document = {'_id': ObjectId(), 'name': 'should be name'}
        self._insert_document(document)

        cursor = Cursor(database=Database(), collection='cursor_test', limit=-1)
        cursor.find(callback=self.stop)

        result, error = self.wait()

        result['_id'].should.be.equal(document['_id'])
        result['name'].should.be.equal(document['name'])
        error.should.be.none

    def test_find_documents_with_limit(self):
        """[CursorTestCase] - Find documents with limit"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1'}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2'}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3'}
        self._insert_document(document3)

        cursor = Cursor(database=Database(), collection='cursor_test', limit=2)
        cursor.find(callback=self.stop)

        result, error = self.wait()

        result.should.have.length_of(2)
        str(result[0]['_id']).should.be.equal(str(document1['_id']))
        str(result[1]['_id']).should.be.equal(str(document2['_id']))
        error.should.be.none

    def test_find_documents_with_spec(self):
        """[CursorTestCase] - Find documents with spec"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1', 'flag': 1}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2', 'flag': 2}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3', 'flag': 1}
        self._insert_document(document3)

        cursor = Cursor(Database(), 'cursor_test', {'flag': 1}, limit=2)
        cursor.find(callback=self.stop)

        result, error = self.wait()

        result.should.have.length_of(2)
        str(result[0]['_id']).should.be.equal(str(document1['_id']))
        str(result[1]['_id']).should.be.equal(str(document3['_id']))
        error.should.be.none

    def test_find_documents_ordering_descending_by_field(self):
        """[CursorTestCase] - Find documents order descending by field"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1', 'size': 1}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2', 'size': 2}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3', 'size': 3}
        self._insert_document(document3)

        cursor = Cursor(database=Database(), collection='cursor_test',
            limit=2, sort={'size': DESCENDING})
        cursor.find(callback=self.stop)

        result, error = self.wait()

        result.should.have.length_of(2)
        str(result[0]['_id']).should.be.equal(str(document3['_id']))
        str(result[1]['_id']).should.be.equal(str(document2['_id']))
        error.should.be.none

    def test_find_documents_ordering_ascending_by_field(self):
        """[CursorTestCase] - Find documents order ascending by field"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1', 'size': 1}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2', 'size': 2}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3', 'size': 3}
        self._insert_document(document3)

        cursor = Cursor(database=Database(), collection='cursor_test',
            limit=2, sort={'size': ASCENDING})
        cursor.find(callback=self.stop)

        result, error = self.wait()

        result.should.have.length_of(2)
        str(result[0]['_id']).should.be.equal(str(document1['_id']))
        str(result[1]['_id']).should.be.equal(str(document2['_id']))
        error.should.be.none

    def test_find_document_by_id(self):
        """[CursorTestCase] - Find document by id"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1', 'size': 1}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2', 'size': 2}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3', 'size': 3}
        self._insert_document(document3)

        cursor = Cursor(Database(), 'cursor_test', document2['_id'], limit=-1)
        cursor.find(callback=self.stop)

        result, error = self.wait()

        str(result['_id']).should.be.equal(str(document2['_id']))
        error.should.be.none

    def test_find_returning_fields(self):
        """[CursorTestCase] - Find and return only selectd fields"""

        document1 = {'_id': ObjectId(), 'name': 'should be name 1',
            'comment': [{'author': 'joe'}, {'author': 'ana'}]}
        self._insert_document(document1)

        document2 = {'_id': ObjectId(), 'name': 'should be name 2',
            'comment': [{'author': 'ana'}]}
        self._insert_document(document2)

        document3 = {'_id': ObjectId(), 'name': 'should be name 3',
            'comment': [{'author': 'june'}]}
        self._insert_document(document3)

        cursor = Cursor(Database(), 'cursor_test', {'comment.author': 'joe'},
            ('comment.$.author', ), limit=-1)
        cursor.find(callback=self.stop)

        result, _ = self.wait()

        keys = result.keys()
        keys.sort()

        keys.should.be.equal(['_id', 'comment'])

        str(result['_id']).should.be.equal(str(document1['_id']))
        result['comment'].should.have.length_of(1)
        result['comment'][0]['author'].should.be.equal('joe')
        _.should.be.none
