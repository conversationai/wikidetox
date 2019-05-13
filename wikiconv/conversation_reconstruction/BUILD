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
