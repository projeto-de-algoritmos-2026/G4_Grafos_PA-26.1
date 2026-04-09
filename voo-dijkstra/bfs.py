from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Iterable
from typing import Any

from price import build_price_graph


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


def _path_price_details(path: tuple[str, ...], price_graph: dict[str, dict[str, float]]) -> tuple[list[dict[str, Any]], float]:
	legs: list[dict[str, Any]] = []
	total = 0.0
	for origin, destination in zip(path, path[1:]):
		price = price_graph.get(origin, {}).get(destination)
		if price is None:
			price = 0.0
		legs.append(
			{
				"from": origin,
				"to": destination,
				"price": round(price, 2),
			}
		)
		total += price
	return legs, round(total, 2)


def _find_top_k_by_connections(
	graph: dict[str, set[str]],
	origin: str,
	destination: str,
	k: int,
	max_connections: int,
	max_expansions: int,
) -> tuple[list[tuple[str, ...]], int, bool]:
	# Enumeracao por prioridade em conexoes com caminho simples e limites de seguranca.
	if origin == destination:
		return [(origin,)], 0, False

	ordered_graph: dict[str, tuple[str, ...]] = {
		node: tuple(sorted(neighbors)) for node, neighbors in graph.items()
	}
	pq: list[tuple[int, tuple[str, ...]]] = [(0, (origin,))]
	found: list[tuple[str, ...]] = []
	expansions = 0
	truncated = False

	while pq and len(found) < k:
		connections, path = heapq.heappop(pq)
		current = path[-1]

		if current == destination:
			found.append(path)
			continue

		if connections >= max_connections:
			continue

		for neighbor in ordered_graph.get(current, ()): 
			if neighbor in path:
				continue
			expansions += 1
			if expansions > max_expansions:
				truncated = True
				pq = []
				break
			heapq.heappush(pq, (connections + 1, path + (neighbor,)))

	return found, expansions, truncated


def find_route_with_fewest_connections(
	airports: list[Any],
	routes: list[Any],
	origin_iata: str,
	destination_iata: str,
) -> dict[str, Any]:
	# Menor numero de trechos usando BFS.
	origin = origin_iata.upper()
	destination = destination_iata.upper()

	graph = _build_unweighted_graph(routes)
	price_graph = build_price_graph(airports, routes)
	max_connections = 10
	max_expansions = 120000
	k = 3

	paths, expansions, truncated = _find_top_k_by_connections(
		graph=graph,
		origin=origin,
		destination=destination,
		k=k,
		max_connections=max_connections,
		max_expansions=max_expansions,
	)

	if not paths:
		return {
			"origin": origin,
			"destination": destination,
			"found": False,
			"message": "Nao foi possivel encontrar rota com os limites atuais de seguranca.",
			"limits": {
				"k": k,
				"max_connections": max_connections,
				"max_expansions": max_expansions,
				"expansions_used": expansions,
				"truncated": truncated,
			},
		}

	routes_payload: list[dict[str, Any]] = []
	for path_tuple in paths:
		legs, total_price = _path_price_details(path_tuple, price_graph)
		routes_payload.append(
			{
				"path": list(path_tuple),
				"connections": len(path_tuple) - 1,
				"legs": legs,
				"total_price": total_price,
			}
		)

	return {
		"origin": origin,
		"destination": destination,
		"found": True,
		"routes": routes_payload,
		"k_requested": k,
		"limits": {
			"max_connections": max_connections,
			"max_expansions": max_expansions,
			"expansions_used": expansions,
			"truncated": truncated,
		},
		"connections": routes_payload[0]["connections"],
		"path": routes_payload[0]["path"],
	}
