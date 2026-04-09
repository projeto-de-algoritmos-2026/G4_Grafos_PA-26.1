from __future__ import annotations

import heapq
from typing import Any

from price import build_price_graph


def _path_price_details(path: tuple[str, ...], graph: dict[str, dict[str, float]]) -> tuple[list[dict[str, Any]], float]:
	legs: list[dict[str, Any]] = []
	total = 0.0
	for origin, destination in zip(path, path[1:]):
		price = graph.get(origin, {}).get(destination)
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


def _path_total_cost(path: tuple[str, ...], graph: dict[str, dict[str, float]]) -> float:
	total = 0.0
	for origin, destination in zip(path, path[1:]):
		edge_cost = graph.get(origin, {}).get(destination)
		if edge_cost is None:
			return float("inf")
		total += edge_cost
	return round(total, 2)


def _shortest_path_with_bans(
	graph: dict[str, dict[str, float]],
	origin: str,
	destination: str,
	banned_edges: set[tuple[str, str]],
	banned_nodes: set[str],
	max_segments: int,
) -> tuple[float, tuple[str, ...]] | None:
	if origin in banned_nodes and origin != destination:
		return None

	ordered_graph: dict[str, tuple[tuple[str, float], ...]] = {
		node: tuple(sorted(neighbors.items())) for node, neighbors in graph.items()
	}
	distances: dict[str, float] = {origin: 0.0}
	parents: dict[str, str | None] = {origin: None}
	pq: list[tuple[float, str]] = [(0.0, origin)]

	while pq:
		current_cost, current_node = heapq.heappop(pq)
		if current_cost > distances.get(current_node, float("inf")):
			continue

		if current_node == destination:
			break

		for neighbor, edge_cost in ordered_graph.get(current_node, ()): 
			if (current_node, neighbor) in banned_edges:
				continue
			if neighbor in banned_nodes and neighbor != destination:
				continue

			new_cost = current_cost + edge_cost
			if new_cost < distances.get(neighbor, float("inf")):
				distances[neighbor] = new_cost
				parents[neighbor] = current_node
				heapq.heappush(pq, (new_cost, neighbor))

	if destination not in distances:
		return None

	path: list[str] = []
	step: str | None = destination
	while step is not None:
		path.append(step)
		step = parents[step]
	path.reverse()

	if len(path) - 1 > max_segments:
		return None

	return round(distances[destination], 2), tuple(path)


def _yen_top_k_paths(
	graph: dict[str, dict[str, float]],
	origin: str,
	destination: str,
	k: int,
	max_segments: int,
) -> tuple[list[tuple[float, tuple[str, ...]]], bool]:
	if origin == destination:
		return [(0.0, (origin,))], False

	first = _shortest_path_with_bans(
		graph=graph,
		origin=origin,
		destination=destination,
		banned_edges=set(),
		banned_nodes=set(),
		max_segments=max_segments,
	)
	if first is None:
		return [], False

	best_paths: list[tuple[float, tuple[str, ...]]] = [first]
	candidates: list[tuple[float, tuple[str, ...]]] = []
	candidate_set: set[tuple[str, ...]] = set()
	truncated = False

	for _ in range(1, k):
		last_cost, last_path = best_paths[-1]
		del last_cost

		for i in range(len(last_path) - 1):
			spur_node = last_path[i]
			root_path = last_path[: i + 1]

			banned_edges: set[tuple[str, str]] = set()
			for _, existing_path in best_paths:
				if len(existing_path) > i and existing_path[: i + 1] == root_path:
					banned_edges.add((existing_path[i], existing_path[i + 1]))

			banned_nodes = set(root_path[:-1])
			spur_result = _shortest_path_with_bans(
				graph=graph,
				origin=spur_node,
				destination=destination,
				banned_edges=banned_edges,
				banned_nodes=banned_nodes,
				max_segments=max_segments,
			)

			if spur_result is None:
				continue

			spur_cost, spur_path = spur_result
			total_path = root_path[:-1] + spur_path
			if len(total_path) - 1 > max_segments:
				continue

			total_cost = _path_total_cost(total_path, graph)
			if total_cost == float("inf"):
				continue

			if total_path not in candidate_set and all(total_path != path for _, path in best_paths):
				heapq.heappush(candidates, (total_cost, total_path))
				candidate_set.add(total_path)

		if not candidates:
			truncated = False
			break

		next_cost, next_path = heapq.heappop(candidates)
		candidate_set.discard(next_path)
		best_paths.append((round(next_cost, 2), next_path))

	if len(best_paths) < k:
		truncated = True

	return best_paths, truncated


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
	k = 3
	max_segments = 10

	found_paths, truncated = _yen_top_k_paths(
		graph=graph,
		origin=origin,
		destination=destination,
		k=k,
		max_segments=max_segments,
	)

	if not found_paths:
		return {
			"origin": origin,
			"destination": destination,
			"found": False,
			"message": "Nao existe caminho entre origem e destino no grafo de precos.",
			"limits": {
				"k": k,
				"max_segments": max_segments,
				"truncated": truncated,
			},
		}

	routes_payload: list[dict[str, Any]] = []
	for total_price, path_tuple in found_paths:
		legs, recomputed_total = _path_price_details(path_tuple, graph)
		routes_payload.append(
			{
				"path": list(path_tuple),
				"segments": len(path_tuple) - 1,
				"legs": legs,
				"total_price": round(total_price if total_price > 0 else recomputed_total, 2),
			}
		)

	return {
		"origin": origin,
		"destination": destination,
		"found": True,
		"routes": routes_payload,
		"k_requested": k,
		"limits": {
			"max_segments": max_segments,
			"truncated": truncated,
		},
		"total_price": routes_payload[0]["total_price"],
		"segments": routes_payload[0]["segments"],
		"path": routes_payload[0]["path"],
	}
