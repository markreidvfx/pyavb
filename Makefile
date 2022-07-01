CYTHON_SRC = $(shell find src/avb -maxdepth 1 -name "*.pyx")
C_SRC = $(CYTHON_SRC:%.pyx=build/cython/%.cpp)
MOD_SOS = $(CYTHON_SRC:%.pyx=%.so)
COVERAGE_EXEC := $(shell command -v coverage 2> /dev/null)

test: python-version
	@python setup.py build_ext --inplace
	@python -m unittest discover tests -v

python-version:
	@python --version

clean:
	- rm -rf build
	- find src/avb -name '*.so' -delete
	- find src/avb -name '*.dylib' -delete
	- find src/avb -name '*.pyd' -delete
	- find src/avb -name '*.dll' -delete
	- find src/avb -name '*.pyc' -delete
	- rm -f src/avb/_ext.cpp
	- rm -f .coverage

doc:
	@make -C docs html

coverage: python-version
ifndef COVERAGE_EXEC
	$(error "coverage command missing: https://coverage.readthedocs.io/en/coverage-4.2/install.html")
endif
	@${COVERAGE_EXEC} run --source=avb -m unittest discover tests
	@${COVERAGE_EXEC} report -m
