# Bazel workspace file.
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "io_bazel_rules_python",
    commit = "fdbb17a4118a1728d19e638a5291b4c4266ea5b8",
    remote = "https://github.com/bazelbuild/rules_python.git",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_import")

# This rule translates the specified bazel-requirements.txt into
# @wikidetox_requirements//:requirements.bzl, which itself exposes a
# pip_install method.
pip_import(
    name = "wikidetox_requirements",
    requirements = "//:requirements-bazel.txt",
)

# Load the pip_install symbol for my_deps, and create the dependencies'
# repositories.
load("@wikidetox_requirements//:requirements.bzl", "pip_install")

pip_install()
