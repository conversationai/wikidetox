package(default_visibility = ["//visibility:public"])

load(
    "@io_bazel_rules_python//python:python.bzl",
    "py_binary",
    "py_library",
    "py_test",
)
load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_binary(
    name = "dataflow_main",
    srcs = ["dataflow_main.py"],
    deps = [
        "//wikiconv/conversation_reconstruction/construct_utils:reconstruct_conversation",
        requirement("apache-beam"),
        requirement("dill"),
    ],
)

py_binary(
    name = "dataflow_content_clean",
    srcs = ["dataflow_content_clean.py"],
    deps = ["//wikiconv/conversation_reconstruction/construct_utils/utils/third_party:clean"],
)

py_library(
    name = "setup",
    srcs = ["setup.py"],
)

py_test(
    name = "dataflow_test",
    srcs = ["dataflow_test.py"],
    data = [
        ":setup",
        ":testdata/edgecases_28_convs/revs_date-5at2001.json",
        ":testdata/edgecases_28_convs/revs_date-6at2001.json",
        ":testdata/edgecases_28_convs/revs_date-7at2001.json",
        ":testdata/edgecases_28_convs/revs_date-8at2001.json",
        ":testdata/edgecases_28_convs/revs_date-9at2001.json",
        ":testdata/empty_init_state/error_logs/error_log",
        ":testdata/empty_init_state/last_revisions/last_rev",
        ":testdata/empty_init_state/page_state",
        ":testdata/empty_init_state/page_states/page_states",
        ":testdata/golden/conversations-00000-of-00001",
        ":testdata/golden/error_log-00000-of-00001",
        ":testdata/golden/last_rev-00000-of-00001",
        ":testdata/golden/page_states-00000-of-00001",
    ],
    deps = [":dataflow_main"],
)
