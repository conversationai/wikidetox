"""
Copyright 2018 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------
A utility class to initialize a database object in Spanner and write to it.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import datetime
from google.cloud import spanner


class SpannerWriter():
    def __init__(self, instance_id, database_id):
      """Initialization of spanner object"""
      self.spanner_client = spanner.Client()
      self.instance_id = instance_id
      self.instance = self.spanner_client.instance(instance_id)
      self.database_id = database_id
      self.database = self.instance.database(database_id)
      self.table_columns = {}

    def create_table(self, table_id, table_columns):
      """Stores table information."""
      self.table_columns[table_id] = table_columns

    def insert_data(self, table_id, data):
      """Inserts data record into spanner."""
      with self.database.batch() as batch:
        batch.insert(
            table = table_id,
            columns = sorted(self.table_columns[table_id].keys()),
            values = self.convert_data(table_id, data))
      return 'Inserted data.'

    def _convert(self, datatype, data):
        if datatype == 'STRING':
          return str(data)
        elif datatype == 'FLOAT':
          return float(data)
        elif datatype == "INT":
          return int(data)
        elif datatype == "BOOL":
          return bool(data)
        elif datatype == "TIMESTAMP":
          try:
            # Records from BigQuery with type timestamp has trailing 0s after
            # second. Hence the hacky solution here to convert it into spanner
            # interpretable timestamp type.
            return datetime.datetime.strptime(data[:19], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")
          except ValueError:
            return data
        else:
          raise Exception("Type %s not recognized." % datatype)


    def convert_data(self, table_id, data):
      ret = {}
      for key, val in self.table_columns[table_id].iteritems():
        if not(key in data) or not(data[key]):
          ret[key] = None
          continue
        if "ARRAY" in val:
          element_type = val[6:-1]
          ret[key] = []
          for x in data[key]:
            ret[key].append(self._convert(element_type, x))
        else:
          ret[key] = self._convert(val, data[key])
      res = []
      for key in sorted(ret.keys()):
        res.append(ret[key])
      return [tuple(res)]

