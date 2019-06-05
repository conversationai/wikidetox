load("@wikidetox_requirements//:requirements.bzl", "requirement")

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
