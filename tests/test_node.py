# coding:utf-8
import unittest
import sure
from mongotor.node import ReadPreference, Node


class ReadPreferenceTestCase(unittest.TestCase):

    def setUp(self):
        class Database:
            dbname = 'test'

        self.primary = Node(host='localhost', port=27027, database=Database)
        self.secondary1 = Node(host='localhost', port=27028, database=Database)
        self.secondary2 = Node(host='localhost', port=27029, database=Database)

        self.primary.available = True
        self.primary.is_primary = True

        self.secondary1.available = True
        self.secondary1.is_secondary = True

    def test_read_preference_default(self):
        """[ReadPreferenceTestCase] - get primary node by default"""
        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary])

        node_found.should.be.eql(self.primary)

    def test_read_preference_primary(self):
        """[ReadPreferenceTestCase] - get primary node when preference is PRIMARY"""
        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.PRIMARY)

        node_found.should.be.eql(self.primary)

    def test_read_preference_primary_preferred_up(self):
        """[ReadPreferenceTestCase] - get primary node when preference is PRIMARY_PREFERRED and primary is up"""

        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.PRIMARY_PREFERRED)

        node_found.should.be.eql(self.primary)

    def test_read_preference_primary_preferred_down(self):
        """[ReadPreferenceTestCase] - get secondary node when preference is PRIMARY_PREFERRED and primary is down"""

        self.primary.available = False
        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.PRIMARY_PREFERRED)

        node_found.should.be.eql(self.secondary1)

    def test_read_preference_secondary(self):
        """[ReadPreferenceTestCase] - get secondary node when preference is SECONDARY"""

        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.SECONDARY)

        node_found.should.be.eql(self.secondary1)

    def test_read_preference_secondary_preferred(self):
        """[ReadPreferenceTestCase] - get secondary node when preference is SECONDARY_PREFERRED"""

        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.SECONDARY_PREFERRED)

        node_found.should.be.eql(self.secondary1)

    def test_read_preference_secondary_preferred_down(self):
        """[ReadPreferenceTestCase] - get primary node when preference is SECONDARY_PREFERRED and secondary is down"""

        self.secondary1.available = False
        node_found = ReadPreference.select_node([self.secondary1,
            self.secondary2, self.primary], ReadPreference.SECONDARY_PREFERRED)

        node_found.should.be.eql(self.primary)