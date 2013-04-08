.SILENT:

all: install_deps test

filename=mongotor-`python -c 'import mongotor;print mongotor.version'`.tar.gz

export PYTHONPATH:=  ${PWD}

MONGOD=mongod
MONGO_DATA=`pwd`/data

mongo-start-node1:
	${MONGOD} --port=27027 --dbpath=${MONGO_DATA}/db/node1 --replSet=mongotor --logpath=${MONGO_DATA}/log/node1.log --fork

mongo-start-node2:
	${MONGOD} --port=27028 --dbpath=${MONGO_DATA}/db/node2 --replSet=mongotor --logpath=${MONGO_DATA}/log/node2.log --fork

mongo-start-arbiter:
	${MONGOD} --port=27029 --dbpath=${MONGO_DATA}/db/arbiter --replSet=mongotor --logpath=${MONGO_DATA}/log/arbiter.log --fork

mongo-start: mongo-kill
	mkdir -p ${MONGO_DATA}/db/node1 ${MONGO_DATA}/db/node2 ${MONGO_DATA}/db/arbiter ${MONGO_DATA}/log
	
	echo "startin mongo instance"
	make mongo-start-node1
	make mongo-start-node2
	make mongo-start-arbiter
	sleep 5

mongo-kill:
	echo "killing mongo instance"
	ps -ef | grep mongo | grep -v grep | grep ${MONGO_DATA} | tr -s ' ' | cut -d ' ' -f 3 | xargs kill -9
	sleep 5

mongo-config:
	mongo localhost:27027 < config-replicaset.js

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
