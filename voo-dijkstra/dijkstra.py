from __future__ import annotations

import heapq
from typing import Any

from price import build_price_graph


def find_shortest_route(
	airports: list[Any],
	routes: list[Any],
	origin_iata: str,
	destination_iata: str,
) -> dict[str, Any]:
	# Menor custo total com Dijkstra no grafo ponderado por preco.
	origin = origin_iata.upper()
	destination = destination_iata.upper()
	graph = build_price_graph(airports, routes)

	if origin == destination:
		return {
			"origin": origin,
			"destination": destination,
			"found": True,
			"total_price": 0.0,
			"path": [origin],
		}

	# Distancias acumuladas e predecessores para reconstruir o caminho.
	distances: dict[str, float] = {origin: 0.0}
	parents: dict[str, str | None] = {origin: None}
	pq: list[tuple[float, str]] = [(0.0, origin)]

	while pq:
		current_cost, current_node = heapq.heappop(pq)

		if current_cost > distances.get(current_node, float("inf")):
			continue

		if current_node == destination:
			break

		for neighbor, edge_cost in graph.get(current_node, {}).items():
			new_cost = current_cost + edge_cost
			if new_cost < distances.get(neighbor, float("inf")):
				distances[neighbor] = new_cost
				parents[neighbor] = current_node
				heapq.heappush(pq, (new_cost, neighbor))

	if destination not in distances:
		return {
			"origin": origin,
			"destination": destination,
			"found": False,
			"message": "Nao existe caminho entre origem e destino no grafo de precos.",
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
		"total_price": round(distances[destination], 2),
		"segments": len(path) - 1,
		"path": path,
	}
