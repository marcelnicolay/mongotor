# from copy import deepcopy
# from tornado import testing
# from tornado.ioloop import IOLoop
# from mongotor.orm import signal
# from mongotor.database import Database
# from mongotor.orm.collection import Collection
# from mongotor.orm.field import StringField, ObjectId, ObjectIdField


# class SignalTestCase(testing.AsyncTestCase):

#     def get_new_ioloop(self):
#         return IOLoop.instance()

#     def setUp(self):
#         super(SignalTestCase, self).setUp()
#         SignalTestCase.signal_triggered = False
#         Database.connect('localhost', 27017, 'asyncmongo_test')

#     def tearDown(self):
#         super(SignalTestCase, self).tearDown()
#         Database.disconnect()

#     def test_save_sends_pre_save_signal_correctly_and_I_can_handle_the_collection_instance(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         @signal.receiver(signal.pre_save, CollectionTest)
#         def collection_pre_save_handler(sender, instance):
#             instance.string_attr += " updated"
#             SignalTestCase.signal_triggered = True

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save(callback=self.stop)

#         self.wait()
#         self.assertTrue(SignalTestCase.signal_triggered)

#         CollectionTest.objects.find_one(collection_test._id, callback=self.stop)
#         collection_found = self.wait()
#         self.assertEquals("should be string value updated", collection_found.string_attr)

#     def test_save_sends_post_save_signal_correctly_and_I_can_handle_the_collection_instance(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         @signal.receiver(signal.post_save, CollectionTest)
#         def collection_post_save_handler(sender, instance):
#             CollectionTest.objects.find_one(collection_test._id, callback=self.stop)
#             collection_found = self.wait()
#             self.assertEquals(instance.string_attr, collection_found.string_attr)
#             SignalTestCase.signal_triggered = True

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save(callback=self.stop)

#         self.wait()
#         self.assertTrue(SignalTestCase.signal_triggered)

#     def test_remove_sends_pre_remove_signal_correctly_and_I_can_handle_the_collection_instance_before_it_dies(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save()

#         @signal.receiver(signal.pre_remove, CollectionTest)
#         def collection_pre_remove_handler(sender, instance):
#             SignalTestCase.instance_copy = deepcopy(instance)
#             SignalTestCase.signal_triggered = True

#         collection_test.remove(callback=self.stop)

#         self.wait()
#         self.assertTrue(SignalTestCase.signal_triggered)
#         self.assertEquals("should be string value", SignalTestCase.instance_copy.string_attr)

#     def test_remove_sends_post_remove_signal_correctly_and_instance_does_not_exists_anymore(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save(callback=self.stop)
#         self.wait()

#         @signal.receiver(signal.post_remove, CollectionTest)
#         def collection_post_remove_handler(sender, instance):
#             CollectionTest.objects.find_one(collection_test._id, callback=self.stop)
#             collection_found = self.wait()
#             self.assertIsNone(collection_found)
#             SignalTestCase.signal_triggered = True

#         collection_test.remove(callback=self.stop)

#         self.wait()
#         self.assertTrue(SignalTestCase.signal_triggered)

#     def test_update_sends_pre_update_signal_correctly(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save(callback=self.stop)

#         self.wait()

#         @signal.receiver(signal.pre_update, CollectionTest)
#         def collection_pre_update_handler(sender, instance):
#             instance.string_attr += ' updated'
#             SignalTestCase.signal_triggered = True

#         collection_test.update(callback=self.stop)
#         self.wait()

#         CollectionTest.objects.find_one(collection_test._id, callback=self.stop)

#         collection_found = self.wait()
#         self.assertEquals("should be string value updated", collection_found.string_attr)
#         self.assertTrue(SignalTestCase.signal_triggered)

#     def test_update_sends_post_update_signal_correctly(self):

#         class CollectionTest(Collection):

#             __collection__ = "collection_test"

#             _id = ObjectIdField()
#             string_attr = StringField()

#         collection_test = CollectionTest()
#         collection_test._id = ObjectId()
#         collection_test.string_attr = "should be string value"
#         collection_test.save()

#         @signal.receiver(signal.post_update, CollectionTest)
#         def collection_post_update_handler(sender, instance):
#             self.assertEquals(collection_test.string_attr, instance.string_attr)
#             SignalTestCase.signal_triggered = True

#         collection_test.update(callback=self.stop)
#         self.wait()

#         self.assertEquals("should be string value", collection_test.string_attr)
#         self.assertTrue(SignalTestCase.signal_triggered)