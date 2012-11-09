# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from bson import ObjectId
from mongotor.pool import ConnectionPool
from mongotor.errors import TooManyConnections
from mongotor import message
import sure


class ConnectionPoolTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_get_connection(self):
        """[ConnectionPoolTestCase] - Can get a connection"""
        pool = ConnectionPool('localhost', 27027, dbname='test')
        pool.connection(self.stop)
        conn = self.wait()

        conn.should.be.a('mongotor.connection.Connection')

    def test_wait_for_connection_when_maxconnection_is_reached(self):
        """[ConnectionPoolTestCase] - Wait for a connection when maxconnections is reached"""

        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=1)

        pool.connection(self.stop)
        conn1 = self.wait()

        pool.connection(self.stop)

        conn1.close()
        conn2 = self.wait()

        conn1.should.be.a('mongotor.connection.Connection')
        conn2.should.be.a('mongotor.connection.Connection')
        pool._connections.should.be.equal(1)

    def test_raise_too_many_connection_when_maxconnection_is_reached(self):
        """[ConnectionPoolTestCase] - Raise TooManyConnections connection when maxconnections is reached"""

        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=10)

        connections = []
        for i in xrange(10):
            pool.connection(self.stop)
            connections.append(self.wait())

        pool.connection(self.stop)
        self.wait.when.called_with().should.throw(TooManyConnections)

    def test_close_connection_stream_should_be_release_from_pool(self):
        """[ConnectionPoolTestCase] - Release connection from pool when stream is closed"""

        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=10)

        pool.connection(self.stop)
        connection = self.wait()

        def release(conn):
            conn.should.be.equal(connection)
            _release(conn)
            self.stop()

        pool._idle_connections.should.have.length_of(9)

        _release = pool.release
        pool.release = release
        connection._stream.close()

        self.wait()

        pool._connections.should.be.equal(9)
        pool._idle_connections.should.have.length_of(9)

    def test_maxusage_in_pool_connections(self):
        """[ConnectionPoolTestCase] - test maxusage in connections"""
        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=1, maxusage=299)

        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': ObjectId()})

        for i in xrange(300):
            pool.connection(self.stop)
            connection = self.wait()

            connection.send_message(message_test, callback=self.stop)
            self.wait()

        pool.connection(self.stop)
        new_connection = self.wait()

        new_connection.usage.should.be.equal(0)
        new_connection.should_not.be.equal(connection)
        new_connection.send_message(message_test, callback=self.stop)

        self.wait()

        new_connection.usage.should.be.equal(1)

    def test_load_in_pool_connections(self):
        """[ConnectionPoolTestCase] - test load in connections"""
        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=10, maxusage=29)

        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': ObjectId()})

        for i in xrange(300):
            pool.connection(self.stop)
            connection = self.wait()

            connection.send_message(message_test, callback=self.stop)
            self.wait()

        pool._idle_connections.should.have.length_of(0)

        for i in xrange(300):
            pool.connection(self.stop)
            connection = self.wait()

            connection.send_message(message_test, callback=self.stop)
            self.wait()

        pool._idle_connections.should.have.length_of(0)

    def test_load_two_in_pool_connections(self):
        """[ConnectionPoolTestCase] - test load two in connections"""
        pool = ConnectionPool('localhost', 27027, dbname='test', maxconnections=10, maxusage=29)

        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': ObjectId()})

        for i in xrange(30000):
            pool.connection(self.stop)
            connection = self.wait()

            connection.send_message(message_test, callback=self.stop)
            self.wait()

        pool._idle_connections.should.have.length_of(0)
