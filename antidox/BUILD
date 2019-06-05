load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_binary(
    name = "perspective",
    srcs = ["perspective.py"],
    deps = [
        requirement("google-api-python-client"),
        requirement("pandas"),
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
