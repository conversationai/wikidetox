#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Setup.py module for the workflow's worker utilities.

All the workflow related code is gathered in a package that will be built as a
source distribution, staged in the staging area for the workflow being run and
then installed in the workers when they start running.

This behavior is triggered by specifying the --setup_file command line option
when running the workflow for remote execution.
"""

from distutils.command.build import build as _build
from distutils.errors import DistutilsError, CCompilerError
import subprocess
import setuptools
from __future__ import print_function
from glob import glob
from os import environ
import sys

if ((sys.version_info[0] == 2 and sys.version_info[1] < 6) or
    (sys.version_info[1] == 3 and sys.version_info[1] < 2)):
    raise RuntimeError("mwparserfromhell needs Python 2.6+ or 3.2+")

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext

from .mwparserfromhell.mwparserfromhell import __version__
from .mwparserfromhell.mwparserfromhell.compat import py26, py3k

with open("README.rst", **({'encoding':'utf-8'} if py3k else {})) as fp:
    long_docs = fp.read()

use_extension = True
fallback = True

# Allow env var WITHOUT_EXTENSION and args --with[out]-extension:

env_var = environ.get("WITHOUT_EXTENSION")
if "--without-extension" in sys.argv:
    use_extension = False
elif "--with-extension" in sys.argv:
    fallback = False
elif env_var is not None:
    if env_var == "1":
        use_extension = False
    elif env_var == "0":
        fallback = False

# Remove the command line argument as it isn't understood by setuptools:

sys.argv = [arg for arg in sys.argv
            if arg != "--without-extension" and arg != "--with-extension"]

def build_ext_patched(self):
    try:
        build_ext_original(self)
    except (DistutilsError, CCompilerError) as exc:
        print("error: " + str(exc))
        print("Falling back to pure Python mode.")
        del self.extensions[:]

if fallback:
    build_ext.run, build_ext_original = build_ext_patched, build_ext.run

# Project-specific part begins here:

tokenizer = Extension("mwparserfromhell.parser._tokenizer",
                      sources=sorted(glob("mwparserfromhell/parser/ctokenizer/*.c")),
                      depends=glob("mwparserfromhell/parser/ctokenizer/*.h"))

setup(
    name = "mwparserfromhell",
    packages = find_packages(exclude=("tests",)),
    ext_modules = [tokenizer] if use_extension else [],
    tests_require = ["unittest2"] if py26 else [],
    test_suite = "tests.discover",
    version = __version__,
    author = "Ben Kurtovic",
    author_email = "ben.kurtovic@gmail.com",
    url = "https://github.com/earwig/mwparserfromhell",
    description = "MWParserFromHell is a parser for MediaWiki wikicode.",
    long_description = long_docs,
    download_url = "https://github.com/earwig/mwparserfromhell/tarball/v{0}".format(__version__),
    keywords = "earwig mwparserfromhell wikipedia wiki mediawiki wikicode template parsing",
    license = "MIT License",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Text Processing :: Markup"
    ],
)


# This class handles the pip install mechanism.
class build(_build):  # pylint: disable=invalid-name
  """A build command class that will be invoked during package install.

  The package built using the current setup.py will be staged and later
  installed in the worker using `pip install package'. This class will be
  instantiated during install for this specific scenario and will trigger
  running the custom commands specified.
  """
  sub_commands = _build.sub_commands + [('CustomCommands', None)]


# Some custom command to run during setup. The command is not essential for this
# workflow. It is used here as an example. Each command will spawn a child
# process. Typically, these commands will include steps to install non-Python
# packages. For instance, to install a C++-based library libjpeg62 the following
# two commands will have to be added:
#
#     ['apt-get', 'update'],
#     ['apt-get', '--assume-yes', install', 'libjpeg62'],
#
# First, note that there is no need to use the sudo command because the setup
# script runs with appropriate access.
# Second, if apt-get tool is used then the first command needs to be 'apt-get
# update' so the tool refreshes itself and initializes links to download
# repositories.  Without this initial step the other apt-get install commands
# will fail with package not found errors. Note also --assume-yes option which
# shortcuts the interactive confirmation.
#
# The output of custom commands (including failures) will be logged in the
# worker-startup log.
CUSTOM_COMMANDS = [
    ['apt-get', 'update'],
    ['apt-get', '--assume-yes', 'install', 'p7zip-full'],
    ['echo', 'Custom command worked!']]
# add the package using custom_command to set it up


class CustomCommands(setuptools.Command):
  """A setuptools Command class able to run arbitrary commands."""

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  def RunCustomCommand(self, command_list):
    print 'Running command: %s' % command_list
    p = subprocess.Popen(
        command_list,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Can use communicate(input='y\n'.encode()) if the command run requires
    # some confirmation.
    stdout_data, _ = p.communicate()
    print 'Command output: %s' % stdout_data
    if p.returncode != 0:
      raise RuntimeError(
          'Command %s failed: exit code: %s' % (command_list, p.returncode))

  def run(self):
    for command in CUSTOM_COMMANDS:
      self.RunCustomCommand(command)


# Configure the required packages and scripts to install.
# Note that the Python Dataflow containers come with numpy already installed
# so this dependency will not trigger anything to be installed unless a version
# restriction is specified.
REQUIRED_PACKAGES = [
    'google-cloud >= 0.27.0',
    'google-cloud-storage >= 1.3.2',
    ]


setuptools.setup(
    name='construct_utils',
    version='0.0.1',
    description='A package to ingest Wikipedia comments.',
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
    cmdclass={
        # Command class instantiated and run during pip install scenarios.
        'build': build,
        'CustomCommands': CustomCommands,
        }
    )

# call setup file for mwparserfromhell
# extra_package
