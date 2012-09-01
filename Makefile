.SILENT:

all: install_deps test

filename=mongotor-`python -c 'import mongotor;print mongotor.version'`.tar.gz

export PYTHONPATH:=  ${PWD}

install_deps:
	pip install -r requirements-dev.txt

test: functional unit

unit: clean
	nosetests -s --verbose --with-coverage --cover-package=mongotor tests/unit/*

functional: clean
	nosetests -s --verbose --with-coverage --cover-package=mongotor tests/functional/*

clean:
	echo "Cleaning up build and *.pyc files..."
	find . -name '*.pyc' -exec rm -rf {} \;
	rm -rf build

release: clean test publish
	printf "Exporting to $(filename)... "
	tar czf $(filename) mongotor setup.py README.md
	echo "DONE!"

publish:
	python setup.py sdist register upload