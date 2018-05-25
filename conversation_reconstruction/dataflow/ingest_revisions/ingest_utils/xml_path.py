"""
Copyright 2017 Google Inc.
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

XML Path.

Holds a representation of an XML path.
"""


class XmlPath(object):
  """Tree addressing into XML.

  Looks lik this: [1]mediawiki-->[5]page-->[4]
  Which should be interpreted as:
    <mediawiki>
      # ... 4 previous things (tags or lines of content) ...
      <page>
      # ... 3 previous things (tags or lines of content) ...
      # --> THIS IS WHERE WE ARE NOW <--

  Invariant: len(self.element_path_pos) == len(self.element_path) + 1
  """

  def __init__(self, copy_from_xml_path=None):
    if copy_from_xml_path is None:
      self.element_path = []
      self.element_path_pos = [0]
    else:
      self.element_path = list(copy_from_xml_path.element_path)
      self.element_path_pos = list(copy_from_xml_path.element_path_pos)

    assert len(self.element_path_pos) == len(self.element_path) + 1

  def __str__(self):
    parts = []
    for i, element_name in enumerate(self.element_path):
      parts.append('[' + str(self.element_path_pos[i]) + ']' + element_name)
    final_element_position = self.element_path_pos[len(self.element_path)]
    parts.append('[' + str(final_element_position) + ']')
    return '-->'.join(parts)

  def __eq__(self, other):
    return (self.element_path == other.element_path and
            self.element_path_pos == other.element_path_pos)

  def element_path_eq(self, other):
    return self.element_path == other.element_path

  def deeper_than(self, other):
    return len(self.element_path_pos) > len(other.element_path_pos)

  def add_line_of_content(self):
    """Note a new additional line of content."""
    self.element_path_pos[len(self.element_path)] += 1

  def enter(self, element_name):
    """Enter an element."""
    self.element_path_pos[len(self.element_path)] += 1
    self.element_path.append(element_name)
    self.element_path_pos.append(0)
    return self

  def enter_many(self, element_names):
    """Enter an element."""
    for n in element_names:
      self.enter(n)
    return self

  def exit(self):
    """Exist the last element."""
    self.element_path_pos.pop()
    self.element_path.pop()
    return self
