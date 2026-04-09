from __future__ import annotations

import math
import random
from collections.abc import Iterable
from typing import Any


EARTH_RADIUS_KM = 6371.0
PRICE_CONSTANT = 0.85
MIN_PERCENTAGE = 0.90
MAX_PERCENTAGE = 1.10


def _get_iata(airport: Any) -> str:
	return str(getattr(airport, "iata", "")).upper()


def _get_coords(airport: Any) -> tuple[float | None, float | None]:
	return getattr(airport, "latitude", None), getattr(airport, "longitude", None)


def _route_origin(route: Any) -> str:
	return str(getattr(route, "origin", "")).upper()


def _route_destination(route: Any) -> str:
	return str(getattr(route, "destination", "")).upper()


def build_airport_index(airports: Iterable[Any]) -> dict[str, Any]:
	# Indexa aeroportos por IATA para acesso rapido durante o calculo.
	index: dict[str, Any] = {}
	for airport in airports:
		iata = _get_iata(airport)
		if iata and iata != "\\N":
			index[iata] = airport
	return index


def spherical_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
	# Distancia entre dois pontos na esfera, ja q a terra é redonda
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	delta_phi = math.radians(lat2 - lat1)
	delta_lambda = math.radians(lon2 - lon1)

	a = (
		math.sin(delta_phi / 2) ** 2
		+ math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
	)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	return EARTH_RADIUS_KM * c


def route_distance_km(origin_airport: Any, destination_airport: Any) -> float | None:
	origin_lat, origin_lon = _get_coords(origin_airport)
	destination_lat, destination_lon = _get_coords(destination_airport)

	if None in {origin_lat, origin_lon, destination_lat, destination_lon}:
		return None

	return spherical_distance_km(origin_lat, origin_lon, destination_lat, destination_lon)


def compute_price(distance_km: float, rng: random.Random | None = None) -> float:
	# Preco baseado em percentual aleatorio entre 60% e 130%, constante e distancia.
	if rng is None:
		rng = random.Random()
	factor = rng.uniform(MIN_PERCENTAGE, MAX_PERCENTAGE)
	return round(distance_km * PRICE_CONSTANT * factor, 2)


def build_price_graph(
	airports: Iterable[Any],
	routes: Iterable[Any],
	seed: int = random.randint(1, 10000),
) -> dict[str, dict[str, float]]:
	# Gera o grafo ponderado por preco; para arestas repetidas, mantem o menor valor.
	airport_index = build_airport_index(airports)
	rng = random.Random(seed)
	graph: dict[str, dict[str, float]] = {}

	for route in routes:
		origin = _route_origin(route)
		destination = _route_destination(route)
		if not origin or not destination or origin == "\\N" or destination == "\\N":
			continue

		origin_airport = airport_index.get(origin)
		destination_airport = airport_index.get(destination)
		if origin_airport is None or destination_airport is None:
			continue

		distance = route_distance_km(origin_airport, destination_airport)
		if distance is None:
			continue

		price = compute_price(distance, rng)
		if origin not in graph:
			graph[origin] = {}

		current = graph[origin].get(destination)
		if current is None or price < current:
			graph[origin][destination] = price

	return graph


def calculate_price(
	airports: list[Any],
	routes: list[Any],
	origin_iata: str,
	destination_iata: str,
) -> dict[str, Any]:
	# Retorna o preco dos voos diretos entre origem e destino.
	graph = build_price_graph(airports, routes)
	origin_key = origin_iata.upper()
	destination_key = destination_iata.upper()

	direct_price = graph.get(origin_key, {}).get(destination_key)
	if direct_price is None:
		return {
			"origin": origin_key,
			"destination": destination_key,
			"has_direct_route": False,
			"message": "Nao existe voo direto com preco calculado para esse par.",
		}

	return {
		"origin": origin_key,
		"destination": destination_key,
		"has_direct_route": True,
		"direct_price": direct_price,
	}
