package(default_visibility = ["//visibility:public"])

py_library(
    name = "conversation_constructor",
    srcs = ["conversation_constructor.py"],
    deps = [
        "//wikiconv/conversation_reconstruction/construct_utils/utils:actions",
        "//wikiconv/conversation_reconstruction/construct_utils/utils:insert_utils",
        "//wikiconv/conversation_reconstruction/construct_utils/utils/third_party:rev_clean",
    ],
)

py_test(
    name = "conversation_constructor_test",
    srcs = ["conversation_constructor_test.py"],
    deps = [
        ":conversation_constructor",
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
