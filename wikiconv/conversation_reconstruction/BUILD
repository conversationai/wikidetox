package(default_visibility = ["//visibility:public"])

py_binary(
    name = "dataflow_main",
    srcs = ["dataflow_main.py"],
    deps = ["//construct_utils:reconstruct_conversation"],
)

py_binary(
    name = "dataflow_content_clean",
    srcs = ["dataflow_content_clean.py"],
    deps = ["//construct_utils/utils/third_party:clean"],
)

py_test(
    name = "dataflow_test",
    srcs = ["dataflow_test.py"],
    deps = [":dataflow_main"],
)
