
pre-release-checks:
	pyroma .

release: export PYTHON_KEYRING_BACKEND := keyring.backends.null.Keyring
release:
	test '$(shell python3 setup.py --version)' = '$(shell git describe --tags)'
	test ! -d dist
	python3 setup.py sdist bdist_wheel
	check-wheel-contents dist
	twine check dist/*
	twine upload dist/*
	mv -i build* *.egg-info dist/.
	mv dist dist.$$(date +%Y-%m-%d.%H%M%S)
	@echo
	@echo Remember to push your git tags too
