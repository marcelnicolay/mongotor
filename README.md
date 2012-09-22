# What is MongoTor ?

(MONGOdb + TORnado) is an asynchronous toolkit for accessing ``MongoDB`` with ``Tornado``.

## Features

* ``ORM`` like to map documents and fields
* Advanced connection management (``replica sets``, slave okay)
* Automatic ``reconnection``
* Connection ``pooling``
* Support for running database commands (``find``, ``find_one``, ``count``, ``sum``, ``mapreduce`` etc...)
* ``Signals`` for pre_save, post_save, pre_remove, post_remove, pre_update and post_update
* 100% of code coverage by test

## Documentation

Visit our online [documentation](http://mongotor.readthedocs.org/) for more examples

## Why not pymongo ?

[PyMongo](http://api.mongodb.org/python/current/) is a recommended way to work with MongoDB in python, but isn't asynchronous and not run inside de tornado's ioloop. If you use pymongo you won't take the advantages of tornado.

## Why not asyncmongo ?

[AsyncMongo](https://github.com/bitly/asyncmongo) is an asynchronous library for accessing mongo with tornado.ioloop, but don't implement replica set, don't have an ORM, I don't like her connection poolin, and i don't trust in your tests. 

Besides, this project is not walking very well, or better, very fast. Exist a lot of issues and pull requests that aren't looked.

I am very thankful to asyncmongo, i worked with it in some projects and it's been served as inspiration, but now, I am very excited to write my own library, more flexible, fast, secure and that will walking faster.

## Installing

```bash
pip install mongotor
```

## Simple usage

```python
import tornado.web
from tornado import gen
from mongotor.database import Database
from bson import ObjectId

class Handler(tornado.web.RequestHandler):

    def initialize(self):
        self.db = Database.connect('localhost:27017', 'mongotor_test')

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        user = {'_id': ObjectId(), 'name': 'User Name'}
        yield gen.Task(self.db.user.insert, user)
        
        yield gen.Task(self.db.user.update, user['_id'], {"$set": {'name': 'New User Name'}})

        user_found = yield gen.Task(self.db.user.find_one, user['_id'])
        assert user_found['name'] == 'New User Name'

        yield gen.Task(self.db.user.remove, user['_id'])
```

## Support to ReplicaSet

```python
import tornado.web
from tornado import gen
from mongotor.database import Database
from mongotor.node import ReadPreference
from bson import ObjectId
import time


class Handler(tornado.web.RequestHandler):

    def initialize(self):
        # configuring an replica set
        self.db = db = Database.connect(["localhost:27027", "localhost:27028"], dbname='mongotor_test',
            read_preference=ReadPreference.SECONDARY_PREFERRED)

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        user = {'_id': ObjectId()}
        
        # write on primary
        yield gen.Task(self.db.user.insert, user)
        
        # wait for replication
        time.sleep(2)

        # read from secondary
        user_found = yield gen.Task(self.db.user.find_one, user['_id'])
        assert user_found == user
```

## Using ORM

```python
from mongotor.orm import collection, field
from mongotor.database import Database

from datetime import datetime
import tornado.web
from tornado import gen

# A connection to the MongoDB database needs to be
# established before perform operations
Database.connect(['localhost:27017','localhost:27018'], 'mongotor_test')

class User(collection.Collection):
    __collection__ = "user"

    _id = field.ObjectIdField()
    name = field.StringField()
    active = field.BooleanField()
    created = field.DateTimeField()

class Handler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        user = User()
        user.name = "User name"
        user.active = True
        user.created = datetime.now()

        yield gen.Task(user.save)

        # update date
        user.name = "New name"
        yield gen.Task(user.update)

        # find one object
        user_found = yield gen.Task(User.objects.find_one, user._id)

        # find many objects
        new_user = User()
        new_user.name = "new user name"
        new_user.user.active = True
        new_user.created = datetime.now()

        users_actives = yield gen.Task(User.objects.find, {'active': True})

        users_actives[0].active = False
        yield gen.Task(users_actives[0].save)

        # remove object
        yield gen.Task(user_found.remove)
```

## Contributing

Write tests for your new feature and send a pull request.

For run mongotor tests install mongodb and do:

```bash
# create a new virtualenv
mkvirtualenv mongotor

# install dev requirements
pip install -r requirements-dev.txt

# start mongo
make mongo-start

# configure replicaset
make mongo-config

# run tests
make test
```

## Issues

Please report any issues via [github issues](https://github.com/marcelnicolay/mongotor/issues)