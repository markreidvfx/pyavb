COVERAGE_EXEC := $(shell command -v coverage 2> /dev/null)

test: python-version
	@python -m unittest discover tests -v

python-version:
	@python --version

clean:
	rm */*.pyc */*/*.pyc

doc:
	@make -C docs html

coverage: python-version
ifndef COVERAGE_EXEC
	$(error "coverage command missing: https://coverage.readthedocs.io/en/coverage-4.2/install.html")
endif
	@${COVERAGE_EXEC} run --source=avb -m unittest discover tests
	@${COVERAGE_EXEC} report -m
