load(
    "@io_bazel_rules_python//python:python.bzl",
    "py_binary",
    "py_library",
    "py_test",
)
load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_binary(
    name = "perspective",
    srcs = ["perspective.py"],
    deps = [
        requirement("python-dateutil"),
        requirement("google-api-python-client"),
        requirement("pandas"),
        requirement("uritemplate"),
    ],
)

py_test(
    name = "perspective_test",
    srcs = ["perspective_test.py"],
    deps = [":perspective"],
)

py_binary(
    name = "wikiwatcher",
    srcs = ["wikiwatcher.py"],
    deps = [
        requirement("sseclient"),
    ],
)

py_test(
    name = "wikiwatcher_test",
    srcs = ["wikiwatcher_test.py"],
    deps = [":wikiwatcher"],
)
