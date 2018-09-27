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

import setuptools

# Configure the required packages and scripts to install.
# Note that the Python Dataflow containers come with numpy already installed
# so this dependency will not trigger anything to be installed unless a version
# restriction is specified.
REQUIRED_PACKAGES = [
    'google-cloud == 0.32.0',
    'google-cloud-storage == 1.6.0',
    'google-apitools == 0.5.22',
    'NoAho==0.9.6.1',
    'mwparserfromhell==0.5.1',
    'yamlconf==0.2.3',
    'mwtypes==0.3.0',
    'beautifulsoup4==4.5.1']

setuptools.setup(
    name='construct_utils',
    version='0.0.1',
    description='A package to reconstruct Wikipedia conversations.',
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
)

