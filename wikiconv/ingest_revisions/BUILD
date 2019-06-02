py_binary(
    name = "dataflow_main",
    srcs = ["dataflow_main.py"],
    deps = ["//wikiconv/ingest_revisions/ingest_utils:wikipedia_revisions_ingester"],
)

# Requires cloud project auth,
# bazel run :dataflow_tester
py_binary(
    name = "dataflow_tester",
    srcs = ["dataflow_tester.py"],
    data = ["testdata/test_wiki_dump.xml.bz2"],
    deps = [
        ":dataflow_main",
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "ingester_test",
    srcs = ["ingester_test.py"],
    data = [
        "testdata/mediawiki_header.xml",
        "testdata/test_wiki_dump.xml",
    ],
    deps = ["//wikiconv/ingest_revisions/ingest_utils:wikipedia_revisions_ingester"],
)
