
release: pyversion != python3 setup.py --version
release: gitversion != git describe --tags
release:
	@echo 'Py version:  $(pyversion)'
	@echo 'Git version: $(gitversion)'
	test '$(pyversion)' = '$(gitversion)'
