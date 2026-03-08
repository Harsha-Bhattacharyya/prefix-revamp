"""Tests for prefix_bootstrap.graph."""

from __future__ import annotations

import networkx as nx
import pytest

from prefix_bootstrap.graph import build_graph, dependency_summary, topological_order
from prefix_bootstrap.packages.base import Package


def _pkg(name: str, depends: list[str] | None = None, stage: int = 1) -> Package:
    return Package(
        name=name,
        version="1.0",
        url=f"https://example.com/{name}-1.0.tar.gz",
        stage=stage,
        depends=depends or [],
    )


class TestBuildGraph:
    def test_simple_graph(self) -> None:
        pkgs = [_pkg("a"), _pkg("b", depends=["a"])]
        g = build_graph(pkgs)
        assert "a" in g.nodes
        assert "b" in g.nodes
        assert g.has_edge("b", "a")

    def test_unknown_dependency_raises(self) -> None:
        pkgs = [_pkg("a", depends=["missing"])]
        with pytest.raises(ValueError, match="unknown dependency"):
            build_graph(pkgs)

    def test_no_edges_for_independent_packages(self) -> None:
        pkgs = [_pkg("a"), _pkg("b"), _pkg("c")]
        g = build_graph(pkgs)
        assert g.number_of_edges() == 0

    def test_graph_is_directed(self) -> None:
        pkgs = [_pkg("a"), _pkg("b", depends=["a"])]
        g = build_graph(pkgs)
        assert isinstance(g, nx.DiGraph)


class TestTopologicalOrder:
    def test_deps_come_before_dependents(self) -> None:
        pkgs = [_pkg("b", depends=["a"]), _pkg("a")]
        ordered = topological_order(pkgs)
        names = [p.name for p in ordered]
        assert names.index("a") < names.index("b")

    def test_chain_order(self) -> None:
        pkgs = [_pkg("c", depends=["b"]), _pkg("b", depends=["a"]), _pkg("a")]
        ordered = topological_order(pkgs)
        names = [p.name for p in ordered]
        assert names.index("a") < names.index("b") < names.index("c")

    def test_single_package(self) -> None:
        pkgs = [_pkg("only")]
        assert topological_order(pkgs) == pkgs

    def test_all_packages_present(self) -> None:
        pkgs = [_pkg("x"), _pkg("y", depends=["x"]), _pkg("z", depends=["y"])]
        ordered = topological_order(pkgs)
        assert {p.name for p in ordered} == {"x", "y", "z"}


class TestDependencySummary:
    def test_returns_string(self) -> None:
        pkgs = [_pkg("a"), _pkg("b", depends=["a"])]
        result = dependency_summary(pkgs)
        assert isinstance(result, str)
        assert "a" in result
        assert "b" in result

    def test_no_deps_shown(self) -> None:
        pkgs = [_pkg("solo")]
        result = dependency_summary(pkgs)
        assert "no dependencies" in result
