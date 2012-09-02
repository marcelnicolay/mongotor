# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from mongotor import message
from bson.objectid import ObjectId
import sure
import fudge


class DatabaseTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(DatabaseTestCase, self).tearDown()
        Database._instance = None

    def test_create_singleton_database_connection(self):
        """[DatabaseTestCase] - Create a singleton database connection"""
        database = Database.connect(["localhost:27017"], dbname='test')

        database._pool.should.be.a('mongotor.pool.ConnectionPool')
        database.should.be.equal(Database())

    def test_raises_error_when_database_was_initiated(self):
        """[DatabaseTestCase] - Raises ValueError when connect to inititated database"""

        Database.connect(["localhost:27017"], dbname='test')
        Database.connect.when.called_with(["localhost:27017"],
            dbname='test').throw(ValueError, 'Database already intiated')

    def test_send_test_message(self):
        """[DatabaseTestCase] - Send a test message to database"""

        Database.connect(["localhost:27017"], dbname='test')

        object_id = ObjectId()
        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': object_id})

        Database().send_message(message_test, self.stop)
        response, error = self.wait()

        result = response['data'][0]

        result['oid'].should.be(object_id)
        result['ok'].should.be(1.0)
        result['str'].should.be(str(object_id))

    @fudge.test
    def test_raises_error_when_cant_send_message(self):
        """[DatabaseTestCase] - Raises error when cant send message"""
        database = Database.connect(["localhost:27017"], dbname='test')
        database._pool = fudge.Fake()

        fake_connection = fudge.Fake('connection')
        fake_connection.expects('send_message').raises(
            ValueError('shoud not be send message'))
        fake_connection.expects('close')

        def fake_connection_method(callback):
            callback(fake_connection)

        database._pool.connection = fudge.Fake(callable=True) \
            .calls(fake_connection_method)

        database.send_message.when.called_with("", callback=None) \
            .throw(ValueError, 'shoud not be send message')

    def test_disconnect_database(self):
        """[DatabaseTestCase] - Disconnect the database"""
        Database.connect(["localhost:27017"], dbname='test')
        Database.disconnect()

        Database._instance.should.be.none

    def test_raises_error_when_disconnect_a_not_connected_database(self):
        """[DatabaseTestCase] - Raises ValueError when disconnect from a not connected database"""
        Database.disconnect.when.called_with().throw(ValueError, "Database isn't connected")
