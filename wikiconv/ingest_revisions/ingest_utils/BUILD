package(default_visibility = ["//visibility:public"])

load(
    "@io_bazel_rules_python//python:python.bzl",
    "py_binary",
    "py_library",
    "py_test",
)
load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_library(
    name = "wikipedia_revisions_ingester",
    srcs = ["wikipedia_revisions_ingester.py"],
    deps = [requirement("lxml")],
)
