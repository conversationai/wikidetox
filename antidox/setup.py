#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License. Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing. software
# distributed under the License is distributed on an "AS IS" BASIS.
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND. either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Setup.py module for the workflow's worker utilities.

All the workflow related code is gathered in a package that will be built as a
source distribution. staged in the staging area for the workflow being run and
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
	'apache-beam==2.12.0',
	'beautifulsoup4==4.6.0',
	'bs4==0.0.1',
	'deltas==0.4.6',
	'diff-match-patch==20181111',
	'future==0.16.0',
	'gax-google-logging-v2==0.8.3',
	'gcloud==0.18.3',
	'google==2.0.1',
	'google-api-core==1.6.0',
	'google-api-python-client==1.7.9',
	'googleapis-common-protos==1.5.3',
	'google-apitools==0.5.26',
	'google-auth==1.5.0',
	'google-cloud-bigquery==1.6.0',
	'google-cloud-core==0.28.1',
	'google-cloud-storage==1.13.0',
	'google-gax==0.12.5',
	'google-reauth==0.1.0',
	'google-resumable-media==0.3.1',
	'grpc-google-logging-v2==0.8.1',
	'lxml==4.2.1',
	'mock==2.0.0',
	'mwparserfromhell==0.5.1',
	'mwtypes==0.3.0',
	'NoAho==0.9.6.1',
	'nose==1.3.7',
	'numpy==1.16.4',
	'oauth2client==2.2.0',
	'pandas==v0.23.4',
	'python-dateutil==2.8.0',
	'requests==2.20.0',
	'setuptools==39.1.0',
	'six==1.11.0',
	'sseclient==0.0.24',
	'uritemplate==3.0.0',
	'urllib3==1.24.2',
	'yamlconf==0.2.3'
]

setuptools.setup(
    name='ingest_utils',
    version='0.0.1',
    description='A package to ingest Wikipedia comments.',
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages()
)
