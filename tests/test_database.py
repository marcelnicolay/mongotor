# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from mongotor.errors import DatabaseError
from mongotor import message
from mongotor import helpers
from bson.objectid import ObjectId
import sure
import fudge


class DatabaseTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(DatabaseTestCase, self).tearDown()
        Database._instance = None

    def test_create_singleton_database_connection_using_connect_method(self):
        """[DatabaseTestCase] - Create a singleton database connection using connect method"""
        database = Database.connect("localhost:27027", dbname='test')

        database.should.be.equal(Database())

    def test_create_singleton_database_connection(self):
        """[DatabaseTestCase] - Create a singleton database connection"""
        database = Database.init("localhost:27027", dbname='test')

        database.should.be.equal(Database())

    def test_not_raise_when_database_was_initiated(self):
        """[DatabaseTestCase] - Not raises ValueError when connect to inititated database"""

        database1 = Database.init("localhost:27027", dbname='test')
        database2 = Database.init("localhost:27027", dbname='test')

        database1.should.be.equal(database2)

    def test_send_test_message(self):
        """[DatabaseTestCase] - Send a test message to database"""

        Database.init(["localhost:27027", "localhost:27028"], dbname='test')

        object_id = ObjectId()
        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': object_id})

        Database().send_message(message_test, callback=self.stop)
        response, _ = self.wait()
        response = helpers._unpack_response(response)

        result = response['data'][0]

        result['oid'].should.be(object_id)
        result['ok'].should.be(1.0)
        result['str'].should.be(str(object_id))

    def test_disconnect_database(self):
        """[DatabaseTestCase] - Disconnect the database"""
        Database.init(["localhost:27027"], dbname='test')
        Database.disconnect()

        Database._instance.should.be.none

    def test_raises_error_when_disconnect_a_not_connected_database(self):
        """[DatabaseTestCase] - Raises ValueError when disconnect from a not connected database"""
        Database.disconnect.when.called_with().throw(ValueError, "Database isn't initialized")

    def test_raises_error_when_could_not_find_node(self):
        """[DatabaseTestCase] - Raises DatabaseError when could not find valid nodes"""

        database = Database.init(["localhost:27030"], dbname='test')

        def send_message():
            database.send_message('', callback=self.stop)
            self.wait()

        send_message.when.called.throw(DatabaseError, 'could not find an available node')

    def test_run_command(self):
        """[DatabaseTestCase] - Run a database command"""

        database = Database.init(["localhost:27027"], dbname='test')
        database.command('ismaster', callback=self.stop)

        response, error = self.wait()
        response['ok'].should.be.ok
