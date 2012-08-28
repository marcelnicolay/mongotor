all: install_deps test

filename=mongotor-`python -c 'import mongotor;print mongotor.version'`.tar.gz

export PYTHONPATH:=  ${PWD}

install_deps:
	@pip install -r requirements.txt

test: functional unit

unit:
	@nosetests -s --verbose --with-coverage --cover-package=mongotor tests/unit/*

functional:
	@nosetests -s --verbose --with-coverage --cover-package=mongotor tests/functional/*

clean:
	@printf "Cleaning up files that are already in .gitignore... "
	@for pattern in `cat .gitignore`; do rm -rf $$pattern; find . -name "$$pattern" -exec rm -rf {} \;; done
	@echo "OK!"

release: clean test publish
	@printf "Exporting to $(filename)... "
	@tar czf $(filename) mongotor setup.py README.md
	@echo "DONE!"

publish:
	@python setup.py sdist register upload