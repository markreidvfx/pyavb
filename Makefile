CYTHON_SRC = $(shell find avb -maxdepth 1 -name "*.pyx")
C_SRC = $(CYTHON_SRC:%.pyx=build/cython/%.cpp)
MOD_SOS = $(CYTHON_SRC:%.pyx=%.so)
COVERAGE_EXEC := $(shell command -v coverage 2> /dev/null)

test: python-version
	@python setup.py build_ext --inplace
	@python -m unittest discover tests -v

test-travis:
	$(TRAVIS_PYTHON_VERSION) --version
	$(TRAVIS_PYTHON_VERSION) setup.py build_ext --inplace
	$(TRAVIS_PYTHON_VERSION) -m unittest discover tests -v

python-version:
	@python --version

clean:
	- rm -rf build
	- find avb -name '*.so' -delete
	- find avb -name '*.dylib' -delete
	- find avb -name '*.pyd' -delete
	- find avb -name '*.dll' -delete
	- find avb -name '*.pyc' -delete

doc:
	@make -C docs html

coverage: python-version
ifndef COVERAGE_EXEC
	$(error "coverage command missing: https://coverage.readthedocs.io/en/coverage-4.2/install.html")
endif
	@${COVERAGE_EXEC} run --source=avb -m unittest discover tests
	@${COVERAGE_EXEC} report -m
