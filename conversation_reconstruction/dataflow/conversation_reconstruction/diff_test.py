"""Tests for diff."""
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from construct_utils.utils.third_party import diff_match_patch as dmp_module
import json

if __name__ == '__main__':
  dmp = dmp_module.diff_match_patch()
  with open("diff_test_document_0.json", "r") as f:
    t1 = json.load(f)
  with open("diff_test_document_1.json", "r") as f:
    t2 = json.load(f)

  diff = dmp.diff_main(t1.encode("utf-8"), t2.encode("utf-8"))
  dmp.diff_cleanupSemantic(diff)
#  delta = dmp.diff_toDelta(diff)
#  print(delta)
  delta = dmp.mydiff_toDelta(diff)
  for d in delta:
      print(d)
  print(len(t1.encode("utf-8")), len(t2.encode("utf-8")))

