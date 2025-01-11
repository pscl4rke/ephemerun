#!/usr/bin/python3


from dataclasses import dataclass
from typing import List, Optional, Protocol

import logging
LOG = logging.getLogger("ephemerun")

import argparse
import random
from shutil import which
import subprocess
import sys


class Backend(Protocol):

    def set_up(self, image: str, volumes: List[str]) -> None:
        ...

    def tear_down(self) -> None:
        ...

    def run_command(self, command: str) -> None:
        ...

    def set_workdir(self, workdir: Optional[str]) -> None:
        ...

    def download(self, path_on_container: str, path_locally: str) -> None:
        ...


class Shell:

    def __init__(self, command: str) -> None:
        self.command = command

    def apply(self, backend: Backend) -> None:
        backend.run_command(self.command)


class Workdir:

    def __init__(self, workdir: str) -> None:
        self.workdir = workdir

    def apply(self, backend: Backend) -> None:
        backend.set_workdir(self.workdir)


class Download:

    def __init__(self, filename: str) -> None:
        if ":" in filename:
            self.srcfile, self.destfile = filename.split(":", 1)
        else:
            self.srcfile = filename
            self.destfile = filename

    def apply(self, backend: Backend) -> None:
        backend.download(self.srcfile, self.destfile)


@dataclass
class DockerPodmanBackend:
    exe: str
    ctrname: str
    # These might need overriding for some base images:
    shell: str = "/bin/sh"
    backgroundjob: str = "sleep 999999"
    # These can be altered:
    workdir: Optional[str] = None

    def set_workdir(self, workdir: Optional[str]) -> None:
        LOG.info("Workdir: %s" % workdir)
        self.workdir = workdir

    def set_up(self, image: str, volumes: List[str]) -> None:
        LOG.info("Starting: %s" % self.ctrname)
        args = [
            self.exe, "run",
            "--rm",
            "--detach",
            "--name", self.ctrname,
            "--entrypoint", self.shell,
        ]
        for volume in volumes:
            args.extend(("--volume", volume))
        args.extend([
            image,
            "-c", self.backgroundjob,
        ])
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL)

    def run_command(self, command: str) -> None:
        LOG.info("Run: %s" % command)
        args = [self.exe, "exec"]
        if self.workdir is not None:
            args.extend(["--workdir", self.workdir])
        args.extend([self.ctrname, self.shell, "-c", command])
        subprocess.run(args, check=True)

    def download(self, path_on_container: str, path_locally: str) -> None:
        LOG.info("Download %r to %r" % (path_on_container, path_locally))
        src = "%s:%s/%s" % (self.ctrname, self.workdir, path_on_container)
        dest = path_locally
        args = [self.exe, "container", "cp", "--archive", src, dest]
        # FIXME check ownership afterwards! Fine with podman, may not be with docker!
        subprocess.run(args, check=True)

    def tear_down(self) -> None:
        LOG.info("Stopping: %s" % self.ctrname)
        args = [
            self.exe, "container", "kill", self.ctrname,
        ]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def __mypy_ensure_DockerPodmanBackend_is_Backend(x: DockerPodmanBackend) -> Backend:
    return x


def suggest_container_name() -> str:
    nonce = "".join(random.choice("0123456789abcdef") for _ in range(10))
    return f"ephemerun-{nonce}"


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.set_defaults(volumes=[], actions=[])
    parser.add_argument("-i", "--image", required=True)
    parser.add_argument("-v", "--volume", action="append", dest="volumes")
    parser.add_argument("-W", "--workdir", action="append", dest="actions", type=Workdir)
    parser.add_argument("-S", "--shellcmd", action="append", dest="actions", type=Shell)
    parser.add_argument("-D", "--download", action="append", dest="actions", type=Download)
    return parser.parse_args(args)


def get_backend(ctrname: str) -> Backend:
    if exe := which("podman"):
        return DockerPodmanBackend(exe, ctrname)
    if exe := which("docker"):
        return DockerPodmanBackend(exe, ctrname)
    raise Exception("No container mechanism found")


def main() -> None:
    logging.basicConfig(level="INFO", format="[ephemerun] %(message)s")
    options = parse_args(sys.argv[1:])
    exitcode = 1
    ctrname = suggest_container_name()
    backend = get_backend(ctrname)
    try:
        backend.set_up(options.image, options.volumes)
        for action in options.actions:
            action.apply(backend)
        LOG.info("All actions completed successfully")
        exitcode = 0
    except KeyboardInterrupt:
        LOG.error("Interrupted")
    except subprocess.CalledProcessError as exc:
        LOG.error("Error: %s" % exc)
    except subprocess.TimeoutExpired as exc:
        LOG.error("Timeout: %s" % exc)
    finally:
        try:
            backend.tear_down()
        except subprocess.CalledProcessError:
            LOG.error("Container teardown failed")
    sys.exit(exitcode)
