package(default_visibility = ["//visibility:public"])

load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_library(
    name = "wikipedia_revisions_ingester",
    srcs = ["wikipedia_revisions_ingester.py"],
    deps = [requirement("lxml")],
)
