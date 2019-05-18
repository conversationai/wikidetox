package(default_visibility = ["//visibility:public"])

py_library(
    name = "conversation_constructor",
    srcs = ["conversation_constructor.py"],
    deps = [
        "//conversation_reconstruction/construct_utils/utils:actions",
        "//conversation_reconstruction/construct_utils/utils:insert_utils",
        "//conversation_reconstruction/construct_utils/utils/third_party:rev_clean",
        "//conversation_reconstruction/construct_utils/utils/third_party/diff_match_patch",
    ],
)

py_library(
    name = "reconstruct_conversation",
    srcs = ["reconstruct_conversation.py"],
    deps = [":conversation_constructor"],
)

py_test(
    name = "reconstruct_conversation_test",
    srcs = ["reconstruct_conversation_test.py"],
    deps = [
        ":conversation_constructor",
        ":reconstruct_conversation",
    ],
)
