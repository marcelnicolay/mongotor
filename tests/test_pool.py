# coding: utf-8
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.pool import ConnectionPool

import sure


class ConnectionPoolTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_get_connection(self):
        """[ConnectionPoolTestCase] - Can get a connection"""
        pool = ConnectionPool(["localhost:27017"], dbname='test')
        pool.connection(self.stop)
        conn = self.wait()

        conn.should.be.a('mongotor.connection.Connection')

    def test_wait_for_connection_when_maxconnection_is_reached(self):
        """[ConnectionPoolTestCase] - Wait for a connection when maxconnections is reached"""

        pool = ConnectionPool(["localhost:27017"], dbname='test', maxconnections=1)

        pool.connection(self.stop)
        conn1 = self.wait()

        pool.connection(self.stop)

        conn1.close()
        conn2 = self.wait()

        conn1.should.be.a('mongotor.connection.Connection')
        conn2.should.be.a('mongotor.connection.Connection')
        pool._connections.should.be.equal(1)
