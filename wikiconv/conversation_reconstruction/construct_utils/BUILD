package(default_visibility = ["//visibility:public"])

load("@wikidetox_requirements//:requirements.bzl", "requirement")

py_library(
    name = "conversation_constructor",
    srcs = ["conversation_constructor.py"],
    deps = [
        "//wikiconv/conversation_reconstruction/construct_utils/utils:actions",
        "//wikiconv/conversation_reconstruction/construct_utils/utils:insert_utils",
        "//wikiconv/conversation_reconstruction/construct_utils/utils/third_party:rev_clean",
        requirement("diff_match_patch"),
        requirement("NoAho"),
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
    deps = [
        ":conversation_constructor",
        requirement("apache-beam"),
        requirement("avro"),
        requirement("fastavro"),
        requirement("google-cloud-core"),
        requirement("google-cloud-storage"),
        requirement("dill"),
        requirement("future"),
        requirement("nose"),
        requirement("numpy"),
        requirement("pyarrow"),
        requirement("typing"),
    ],
)

py_test(
    name = "reconstruct_conversation_test",
    srcs = ["reconstruct_conversation_test.py"],
    deps = [
        ":conversation_constructor",
        ":reconstruct_conversation",
    ],
)
