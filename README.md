
# Ephemerun

>   Incredibly temporary containers

Ephemerun wraps around an existing container system on your computer.
It lets you run a single one-liner which spins up a container,
does a series of things in it, and then tears it all down again afterwards.

It is a good way to run a test suite.
It is particularly good at running the tests multiple times using
slightly different base images
(e.g. to ensure compatibility with multiple platform versions).
It also has support for building artefacts in a container and
downloading them out to the host system.

It is especially helpful when combined with `make`.
There is no good way to define a teardown recipe in a Makefile,
so if you spin up a container and one of your actions fails
`make` will stop and leave your "temporary" container permanently
floating around.
But Ephemerun will always tidy up after itself so can be safely called
from a Makefile.

## Installation

This codebase is available  on PyPI:

    $ pip install ephemerun

but can also be installed straight from the Git source:

    $ pip install git+https://github.com/pscl4rke/ephemerun.git

## Example Usage

Silly demo:

    $ ephemerun \
        -i python:3.9-slim-bullseye \
        -S pwd \
        -W /tmp \
        -S pwd

Real-world example of running tests:

    $ ephemerun \
        -i "python:3.9-slim-bullseye" \
        -v "$(pwd):/root/src:ro" \
        -W "/root" \
        -S "cp -air ./src/* ." \
        -S "pip --no-cache-dir install .[testing]" \
        -S "mypy --cache-dir /dev/null projectdir" \
        -S "coverage run -m unittest discover tests/" \
        -S "coverage report -m"

Real-world example of building an artefact:

    $ ephemerun \
        -i "docker.io/library/golang:1.23" \
        -v "$(pwd):/root/src:ro" \
        -W "/root" \
        -S "cp -air ./src/* ." \
        -S "go build hello.go" \
        -D hello
    $ ./hello

## Quick Docs

* Use `-i` to set the base image for the temporary container.
* Use `-v` to mount a directory into it (where the `:ro` suffix
makes it readonly).
* Run `-W` to change the current working directory.
* Run `-S` to execute a line in a shell.
* Run `-D` to download a file out of the container (with
a `:destname` suffix if you want a different name).
* And of course `-h` gives you usage info!

## Roadmap

* The output would be easier to read if Epheruns's messages
were coloured in.

* Currently only Docker and Podman are available as backends
and ephemerun autodetects which one is installed.
Perhaps Containerd or something using a Kubernetes cluster
could be added without too much difficulty.
I would like to support many other mechanisms too
(e.g. Systemd Nspawn)
but currently everything assumes the image is specified
in OCI format.

* It would be good to mirror `-D` with an inverse `-U`
to do an upload.

* I *think* if `-D` is used with the docker backend the files
will end up being owned by a different user from the one running
ephemerun.
I think that is undesirable.

* As the examples show there is an icky problem where the current
directory is mounted readonly,
but then build commands etc fail,
so we have to mount it to a `src/` subdirectory and copy the files out.
Surely there is a better way.

* Many tools can make use of a cache,
but anything that gets cached is thrown away by Ephemerun.
I do not have a strategy for handling that at the moment.

* More generally we could do with developing and documenting a strategy
for one Makefile recipe to build a reusable image
and then different recipes using it for different purposes.
Presumably ephemerun wouldn't be used for the building.

## Licence

This code is licensed under the terms of the
GNU General Public Licence version 3.
