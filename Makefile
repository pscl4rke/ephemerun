
pre-release-checks:
	pyroma .

release:
	test '$(shell python3 setup.py --version)' = '$(shell git describe --tags)'
