# What is MongoTor ?

(MONGO + TORnado) is an asynchronous toolkit for accessing mongo with tornado.

## Features

* ORM like to map documents and fields
* Advanced connection management (replica sets, slave okay)
* Automatic reconnection
* Connection pooling
* Support for running database commands (find, find_one, count, sum, mapreduce etc...)
* Signals for pre_save, post_save, pre_remove, post_remove, pre_update and post_update
* 100% of code coverage by test

## Why not pymongo ?

[PyMongo](http://api.mongodb.org/python/current/) is a recommended way to work with MongoDB in python, but isn't asynchronous and not run inside de tornado's ioloop. If you use pymongo you won't take the advantages of tornado.

## Why not asyncmongo ?

[AsyncMongo](https://github.com/bitly/asyncmongo) is asynchronous library for accessing mongo with tornado.ioloop, but don't implement replica set, don't have an ORM, I don't like her connection pooling, is deficitary, and i don't trust in your tests. 

Besides, this project is not walking very well, or better, very fast. Exist a lot of issues and pull requests that aren't looked.

I am very thankful to asyncmongo, i worked with he in some projects and he's been served as inspiration, but now, I am very excited to write my own library, more flexible, fast, secure and that will walking faster.

## Installing

    pip install mongotor

## Using

    from mongotor.orm import Collection
    from mongotor.orm.field import StringField, ObjectIdField, BooleanField, DateTimeField
    from mongotor.database import Database

    from datetime import datetime
    import tornado.web
    from tornado import gen

    # A connection to the MongoDB database needs to be established before perform operations
    # A connection is stabilished using a Databse object
    Database.connect(['localhost:27017','localhost:27018'], 'asyncmongo_test')
    
    class User(Collection):

        __collection__ = "user"

        _id = ObjectIdField()
        name = StringField()
        active = BooleanField()
        created = DateTimeField()

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

## Contributing

Send a pull request (preferred) or patches using ``git format-patch``. Please, write unit and/or functional tests for your new feature.

## Issues

Please report any issues via [github issues](https://github.com/marcelnicolay/mongotor/issues)