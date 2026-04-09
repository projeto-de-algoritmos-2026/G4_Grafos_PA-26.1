from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any


def _route_origin(route: Any) -> str:
	return str(getattr(route, "origin", "")).upper()


def _route_destination(route: Any) -> str:
	return str(getattr(route, "destination", "")).upper()


def _build_unweighted_graph(routes: Iterable[Any]) -> dict[str, set[str]]:
	# Grafo simples para BFS (cada aresta representa 1 conexao).
	graph: dict[str, set[str]] = {}
	for route in routes:
		origin = _route_origin(route)
		destination = _route_destination(route)
		if not origin or not destination or origin == "\\N" or destination == "\\N":
			continue
		graph.setdefault(origin, set()).add(destination)
	return graph


def find_route_with_fewest_connections(
	airports: list[Any],
	routes: list[Any],
	origin_iata: str,
	destination_iata: str,
) -> dict[str, Any]:
	# Menor numero de trechos usando BFS.
	del airports
	origin = origin_iata.upper()
	destination = destination_iata.upper()

	if origin == destination:
		return {
			"origin": origin,
			"destination": destination,
			"connections": 0,
			"path": [origin],
		}

	graph = _build_unweighted_graph(routes)
	queue: deque[str] = deque([origin])
	parents: dict[str, str | None] = {origin: None}

	while queue:
		current = queue.popleft()
		if current == destination:
			break

		for neighbor in graph.get(current, set()):
			if neighbor in parents:
				continue
			parents[neighbor] = current
			queue.append(neighbor)

	if destination not in parents:
		return {
			"origin": origin,
			"destination": destination,
			"found": False,
			"message": "Nao existe rota entre origem e destino no grafo de conexoes.",
		}

	path: list[str] = []
	step: str | None = destination
	while step is not None:
		path.append(step)
		step = parents[step]
	path.reverse()

	return {
		"origin": origin,
		"destination": destination,
		"found": True,
		"connections": len(path) - 1,
		"path": path,
	}
