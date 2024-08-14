
# Ephemerun

>   Incredibly temporary containers

Ephemerun wraps around an existing container system on your computer.
It lets you run a single one-liner which spins up a container,
does a series of things in it, and then tears it all down again afterwards.

It is a good way to run a test suite.
It is particularly good at running the tests multiple times using
slightly different base images
(e.g. to ensure compatibility with multiple platform versions).
In the future it might be good for building artefacts too.

It is especially helpful when combined with `make`.
There is no good way to define a teardown recipe in a Makefile,
so if you spin up a container and one of your actions fails
`make` will stop and leave your "temporary" container permanently
floating around.

## Installation

This codebase is not (currently) on PyPI,
but can be installed with pip straight from the Git source:

    $ pip install git+https://github.com/pscl4rke/ephemerun.git

## Example Usage

Silly demo:

    $ ephemerun \
        -i python:3.9-slim-bullseye \
        -S pwd \
        -W /tmp \
        -S pwd

Real-world example:

    $ ephemerun \
        -i "python:3.9-slim-bullseye" \
        -v "$(pwd):/root/src:ro" \
        -W "/root" \
        -S "cp -air ./src/* ." \
        -S "pip --no-cache-dir install .[testing]" \
        -S "mypy --cache-dir /dev/null projectdir" \
        -S "coverage run -m unittest discover tests/" \
        -S "coverage report -m"

## Quick Docs

* Use `-i` to set the base image for the temporary container.
* Use `-v` to mount a directory into it (where the `:ro` suffix
makes it readonly).
* Run `-W` to change the current working directory.
* Run `-S` to execute a line in a shell.
* And of course `-h` gives you usage info!

## Roadmap

* The output would be easier to read if Epheruns's messages
were coloured in.

* Currently only Docker is available as a backend.
It would be fairly easy to add Podman support.
Perhaps Containerd too.
I would like to support other mechanisms too
(e.g. Systemd Nspawn)
but currently everything assumes the image is specified
in OCI format.

* Currently the only useful thing you can do is run shell commands
with `-S` and capture the stdout/stderr output.
I would like to add a "download" mechanism,
so artefacts can be built in a container and then copied out
to the host.
Presumably an "upload" mechanism would be easy to add at the
same time.

* Many tools can make use of a cache,
but anything that gets cached is thrown away by Ephemerun.
I do not have a strategy for handling that at the moment.

## Licence

This code is licensed under the terms of the
GNU General Public Licence version 3.
