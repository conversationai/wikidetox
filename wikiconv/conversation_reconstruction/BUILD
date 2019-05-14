package(default_visibility = ["//visibility:public"])

py_binary(
    name = "dataflow_main",
    srcs = ["dataflow_main.py"],
)

py_test(
    name = "dataflow_test",
    srcs = ["dataflow_test.py"],
    deps = [":dataflow_main"],
)

py_test(
    name = "constructor_tester",
    srcs = ["constructor_tester.py"],
    deps = ["//conversation_reconstruction/construct_utils:conversation_constructor"],
    data = [":testdata/reversed_page_14677358.json"],
)