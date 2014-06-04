.SILENT:

all: install_deps test

filename=mongotor-`python -c 'import mongotor;print mongotor.version'`.tar.gz

export PYTHONPATH:=  ${PWD}

MONGOD=mongod
MONGO_DATA=`pwd`/data

mongo-start-node1:
	${MONGOD} --port=27027 --dbpath=${MONGO_DATA}/db/node1 --replSet=mongotor --logpath=${MONGO_DATA}/log/node1.log --fork --smallfiles --oplogSize 30 --nojournal

mongo-start-node2:
	${MONGOD} --port=27028 --dbpath=${MONGO_DATA}/db/node2 --replSet=mongotor --logpath=${MONGO_DATA}/log/node2.log --fork --smallfiles --oplogSize 30 --nojournal

mongo-start-arbiter:
	${MONGOD} --port=27029 --dbpath=${MONGO_DATA}/db/arbiter --replSet=mongotor --logpath=${MONGO_DATA}/log/arbiter.log --fork --smallfiles --oplogSize 30 --nojournal

mongo-restart: mongo-kill mongo-start

mongo-start:
	mkdir -p ${MONGO_DATA}/db/node1 ${MONGO_DATA}/db/node2 ${MONGO_DATA}/db/arbiter ${MONGO_DATA}/log
	
	echo "starting mongo instance"
	make mongo-start-node1
	make mongo-start-node2
	make mongo-start-arbiter
	echo 'Waiting 10s for `mongod`s to start'
	sleep 10

mongo-kill-node1:
	ps -eo pid,args | grep 27027 | grep ${MONGO_DATA} | grep -v grep | awk '{print $$1}' | xargs kill 2> /dev/null | true

mongo-kill-node2:
	ps -eo pid,args | grep 27028 | grep ${MONGO_DATA} | grep -v grep | awk '{print $$1}' | xargs kill 2> /dev/null | true

mongo-kill-arbiter:
	ps -eo pid,args | grep 27029 | grep ${MONGO_DATA} | grep -v grep | awk '{print $$1}' | xargs kill 2> /dev/null | true

mongo-kill:
	echo "killing mongo instance"
	make mongo-kill-node1
	make mongo-kill-node2
	make mongo-kill-arbiter
	echo 'Waiting 1s for `mongod`s to stop'
	sleep 1

mongo-config:
	mongo localhost:27027 < config-replicaset.js
	echo 'Waiting 40s to let replicaset elect a primary'
	sleep 40

install_deps:
	pip install -r requirements-dev.txt

test: clean
	nosetests

clean:
	echo "Cleaning up build and *.pyc files..."
	find . -name '*.pyc' -exec rm -rf {} \;

release: clean test publish
	printf "Exporting to $(filename)... "
	tar czf $(filename) mongotor setup.py README.md
	echo "DONE!"

publish:
	python setup.py sdist register upload
