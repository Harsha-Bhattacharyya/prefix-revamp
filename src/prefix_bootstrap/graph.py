"""
prefix_bootstrap.graph
~~~~~~~~~~~~~~~~~~~~~~

Dependency-graph helpers backed by *networkx*.

``build_graph(packages)`` constructs a directed acyclic graph (DAG) where each
node is a package name and each edge ``A -> B`` means "A depends on B" (i.e.
B must be built before A).

``topological_order(packages)`` returns the packages sorted so that every
package's dependencies appear before it.

If there is a cycle in the dependency declarations the functions raise
``networkx.exception.NetworkXUnfeasible``.
"""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx
import structlog

from prefix_bootstrap.packages.base import Package

log = structlog.get_logger(__name__)


def build_graph(packages: Iterable[Package]) -> nx.DiGraph[str]:
    """Build a directed dependency graph from *packages*.

    Nodes are package names (``str``).  An edge ``(A, B)`` means package *A*
    depends on package *B* (i.e. *B* must be installed first).

    Parameters
    ----------
    packages:
        Iterable of :class:`~prefix_bootstrap.packages.base.Package` objects.

    Returns
    -------
    nx.DiGraph[str]
        The dependency graph.

    Raises
    ------
    ValueError
        If a package declares a dependency that is not in *packages*.
    """
    pkg_list = list(packages)
    known = {p.name for p in pkg_list}
    graph: nx.DiGraph[str] = nx.DiGraph()

    for pkg in pkg_list:
        graph.add_node(pkg.name, package=pkg)

    for pkg in pkg_list:
        for dep in pkg.depends:
            if dep not in known:
                raise ValueError(
                    f"Package '{pkg.name}' declares unknown dependency '{dep}'.  "
                    "Please add it to the catalogue. :/"
                )
            graph.add_edge(pkg.name, dep)

    log.debug(
        "graph.built",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )
    return graph


def topological_order(packages: Iterable[Package]) -> list[Package]:
    """Return *packages* sorted in safe build order.

    Packages with no dependencies come first; each package appears only after
    all of its transitive dependencies.

    Parameters
    ----------
    packages:
        Iterable of :class:`~prefix_bootstrap.packages.base.Package` objects.

    Returns
    -------
    list[Package]
        Packages in topological (build) order.

    Raises
    ------
    networkx.exception.NetworkXUnfeasible
        If the dependency graph contains a cycle.
    """
    pkg_list = list(packages)
    graph = build_graph(pkg_list)
    pkg_map = {p.name: p for p in pkg_list}

    ordered_names: list[str] = list(reversed(list(nx.topological_sort(graph))))
    result = [pkg_map[name] for name in ordered_names]

    log.debug("graph.topological_order", order=[p.name for p in result])
    return result


def dependency_summary(packages: Iterable[Package]) -> str:
    """Return a human-readable dependency tree as a multi-line string.

    Useful for ``--dry-run`` / ``--show-deps`` output.
    """
    pkg_list = list(packages)
    graph = build_graph(pkg_list)

    lines: list[str] = []
    for name in nx.topological_sort(graph):
        deps = list(graph.successors(name))
        if deps:
            lines.append(f"  {name}  ->  {', '.join(deps)}")
        else:
            lines.append(f"  {name}  (no dependencies)")
    return "\n".join(lines)
