# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.pool import ConnectionPool
from mongotor.errors import TooManyConnections
import time
import sure
import os


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

        pool._connections.should.be.equal(1)

        def release(conn):
            conn.should.be.equal(connection)
            _release(conn)
            self.stop()

        _release = pool.release
        pool.release = release
        connection._stream.close()

        self.wait()

        pool._connections.should.be.equal(1)
        pool._idle_connections.should.have.length_of(1)
        pool._idle_connections[0].should.be.equal(connection)
