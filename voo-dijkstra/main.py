from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
AIRPORTS_FILE = DATA_DIR / "airports.dat"
ROUTES_FILE = DATA_DIR / "routes.dat"


@dataclass(frozen=True)
class Airport:
	airport_id: str
	name: str
	city: str
	country: str
	iata: str
	icao: str
	latitude: float | None
	longitude: float | None


@dataclass(frozen=True)
class Route:
	airline: str
	airline_id: str
	origin: str
	origin_id: str
	destination: str
	destination_id: str
	codeshare: str
	stops: str
	equipment: str


def normalize_text(value: str) -> str:
	# Normaliza texto para comparacoes flexiveis.
	return re.sub(r"\s+", " ", value.strip().lower())


def parse_float(value: str) -> float | None:
	# Converte texto para float, retornando None quando o valor for invalido.
	try:
		if value.strip() in {"", "\\N"}:
			return None
		return float(value)
	except ValueError:
		return None


def load_airports(path: Path) -> list[Airport]:
	# Carrega o dataset de aeroportos.
	airports: list[Airport] = []
	with path.open(newline="", encoding="utf-8") as file_handle:
		reader = csv.reader(file_handle)
		for row in reader:
			if len(row) < 8:
				continue
			airports.append(
				Airport(
					airport_id=row[0],
					name=row[1],
					city=row[2],
					country=row[3],
					iata=row[4],
					icao=row[5],
					latitude=parse_float(row[6]),
					longitude=parse_float(row[7]),
				)
			)
	return airports


def load_routes(path: Path) -> list[Route]:
	# Carrega o dataset de rotas.
	routes: list[Route] = []
	with path.open(newline="", encoding="utf-8") as file_handle:
		reader = csv.reader(file_handle)
		for row in reader:
			if len(row) < 9:
				continue
			routes.append(
				Route(
					airline=row[0],
					airline_id=row[1],
					origin=row[2],
					origin_id=row[3],
					destination=row[4],
					destination_id=row[5],
					codeshare=row[6],
					stops=row[7],
					equipment=row[8],
				)
			)
	return routes


def airport_matches(airports: Iterable[Airport], query: str) -> list[Airport]:
	# Busca aeroportos por IATA, ICAO, nome ou cidade.
	normalized_query = normalize_text(query)
	upper_query = query.strip().upper()

	# Prioriza codigo exato para evitar falsos positivos por substring.
	if upper_query:
		exact_code_matches = [
			airport
			for airport in airports
			if airport.iata.upper() == upper_query or airport.icao.upper() == upper_query
		]
		if exact_code_matches:
			return exact_code_matches

	matches: list[Airport] = []

	for airport in airports:
		if upper_query:
			if airport.iata.upper().startswith(upper_query) or airport.icao.upper().startswith(upper_query):
				matches.append(airport)
				continue

		airport_tokens = [
			normalize_text(airport.name),
			normalize_text(airport.city),
			normalize_text(airport.country),
			normalize_text(airport.icao),
		]

		if any(normalized_query in token for token in airport_tokens):
			matches.append(airport)

	return matches


def select_airport(airports: list[Airport], prompt_text: str) -> Airport:
	# Permite selecionar um aeroporto com ajuda do usuario.
	while True:
		raw_query = input(prompt_text).strip()
		matches = airport_matches(airports, raw_query)

		if not matches:
			print("Nenhum aeroporto encontrado. Tente novamente usando IATA, nome ou cidade.")
			continue

		if len(matches) == 1:
			return matches[0]

		print("Foram encontrados varios aeroportos:")
		for index, airport in enumerate(matches, start=1):
			print(f"{index}. {airport.name} - {airport.city} - {airport.country} ({airport.iata}/{airport.icao})")

		choice = input("Escolha o numero do aeroporto desejado: ").strip()
		if choice.isdigit():
			selected_index = int(choice)
			if 1 <= selected_index <= len(matches):
				return matches[selected_index - 1]

		print("Opcao invalida. Tente novamente.")


def direct_routes(routes: Iterable[Route], origin_iata: str, destination_iata: str) -> list[Route]:
	# Filtra rotas diretas entre origem e destino.
	return [
		route
		for route in routes
		if route.origin.upper() == origin_iata.upper() and route.destination.upper() == destination_iata.upper()
	]


def outgoing_routes(routes: Iterable[Route], origin_iata: str) -> list[Route]:
	# Filtra todas as saidas da origem.
	return [route for route in routes if route.origin.upper() == origin_iata.upper()]


def incoming_routes(routes: Iterable[Route], destination_iata: str) -> list[Route]:
	# Filtra todas as entradas no destino.
	return [route for route in routes if route.destination.upper() == destination_iata.upper()]


def one_stop_connections(routes: Iterable[Route], origin_iata: str, destination_iata: str) -> list[tuple[Route, Route]]:
	# Monta conexoes de uma parada quando necessario.
	routes_by_origin: dict[str, list[Route]] = {}
	for route in routes:
		routes_by_origin.setdefault(route.origin.upper(), []).append(route)

	connections: list[tuple[Route, Route]] = []
	for first_leg in outgoing_routes(routes, origin_iata):
		second_legs = routes_by_origin.get(first_leg.destination.upper(), [])
		for second_leg in second_legs:
			if second_leg.destination.upper() == destination_iata.upper():
				connections.append((first_leg, second_leg))
	return connections


def print_route_summary(label: str, route_list: Iterable[Route]) -> None:
	# Exibe um resumo simples de rotas.
	route_list = list(route_list)
	print(f"\n{label}")
	if not route_list:
		print("Nenhuma rota encontrada.")
		return

	for index, route in enumerate(route_list, start=1):
		print(
			f"{index}. {route.origin} -> {route.destination} | "
			f"companhia {route.airline} | paradas {route.stops} | equipamento {route.equipment}"
		)


def print_connection_summary(label: str, connections: Iterable[tuple[Route, Route]]) -> None:
	# Exibe um resumo simples de conexoes.
	connections = list(connections)
	print(f"\n{label}")
	if not connections:
		print("Nenhuma conexao encontrada.")
		return

	for index, (first_leg, second_leg) in enumerate(connections, start=1):
		print(
			f"{index}. {first_leg.origin} -> {first_leg.destination} -> {second_leg.destination} | "
			f"companhias {first_leg.airline} / {second_leg.airline}"
		)


def fastest_routes_by_filter(routes: Iterable[Route], origin_iata: str, destination_iata: str) -> list[Route]:
	# Seleciona rotas mais rapidas por filtro do dataset.
	filtered_routes = direct_routes(routes, origin_iata, destination_iata)
	zero_stop_routes = [route for route in filtered_routes if route.stops == "0"]
	if zero_stop_routes:
		return zero_stop_routes
	return filtered_routes


def bfs_min_connections(airports: list[Airport], routes: list[Route], origin_iata: str, destination_iata: str):
	# Chama a rotina de BFS para menor numero de conexoes.
	import bfs

	solver = getattr(bfs, "find_route_with_fewest_connections", None)
	if not callable(solver):
		raise NotImplementedError(
			"Implemente bfs.find_route_with_fewest_connections(airports, routes, origin_iata, destination_iata) em bfs.py."
		)

	return solver(airports=airports, routes=routes, origin_iata=origin_iata, destination_iata=destination_iata)


def price_formula(airports: list[Airport], routes: list[Route], origin_iata: str, destination_iata: str):
	# Chama a formula de gerar preco aleatorio.
	import price

	solver = getattr(price, "calculate_price", None)
	if not callable(solver):
		raise NotImplementedError(
			"Implemente price.calculate_price(airports, routes, origin_iata, destination_iata) em price.py."
		)

	return solver(airports=airports, routes=routes, origin_iata=origin_iata, destination_iata=destination_iata)


def dijkstra(airports: list[Airport], routes: list[Route], origin_iata: str, destination_iata: str):
	# Chama o algorítmo de Dijkstra para calcular a rota mais barata.
	import dijkstra

	solver = getattr(dijkstra, "find_shortest_route", None)
	if not callable(solver):
		raise NotImplementedError(
			"Implemente dijkstra.find_shortest_route(airports, routes, origin_iata, destination_iata) em dijkstra.py."
		)

	return solver(airports=airports, routes=routes, origin_iata=origin_iata, destination_iata=destination_iata)


def same_city_alternatives(airports: Iterable[Airport], destination: Airport, max_options: int = 5) -> list[Airport]:
	# Sugere aeroportos alternativos da mesma cidade para evitar buscas sem resultado.
	city_key = normalize_text(destination.city)
	country_key = normalize_text(destination.country)
	selected_iata = destination.iata.upper()
	alternatives: list[Airport] = []
	seen_codes: set[str] = set()

	for airport in airports:
		iata = airport.iata.upper()
		if not iata or iata == "\\N" or iata == selected_iata:
			continue
		if normalize_text(airport.city) != city_key or normalize_text(airport.country) != country_key:
			continue
		if iata in seen_codes:
			continue
		seen_codes.add(iata)
		alternatives.append(airport)

	alternatives.sort(key=lambda airport: (airport.name, airport.iata))
	return alternatives[:max_options]


def find_first_working_alternative(
	airports: list[Airport],
	routes: list[Route],
	origin_iata: str,
	destination: Airport,
	solver,
) -> tuple[Airport | None, dict[str, Any] | None]:
	# Tenta aeroportos alternativos da mesma cidade ate encontrar rota valida.
	for alternative in same_city_alternatives(airports, destination):
		result = solver(airports, routes, origin_iata, alternative.iata)
		if result.get("found"):
			return alternative, result
	return None, None


def print_ranked_routes(title: str, result: dict[str, Any], metric_key: str, metric_label: str) -> None:
	# Exibe rotas ranqueadas com detalhe de cada trecho e total.
	print(f"\n{title}")
	if not result.get("found"):
		print(result.get("message", "Nenhuma rota encontrada."))
		limits = result.get("limits", {})
		if limits:
			parts: list[str] = []
			if "max_expansions" in limits:
				parts.append(f"expansoes={limits.get('expansions_used', 0)}/{limits.get('max_expansions', '-')}")
			if "max_connections" in limits:
				parts.append(f"profundidade={limits.get('max_connections')}")
			elif "max_segments" in limits:
				parts.append(f"profundidade={limits.get('max_segments')}")
			if parts:
				print(f"Limites usados: {', '.join(parts)}.")
		return

	routes = result.get("routes", [])
	if not routes:
		print("Nenhuma rota encontrada.")
		return

	for index, route in enumerate(routes, start=1):
		path = route.get("path", [])
		metric_value = route.get(metric_key, "-")
		total_price = route.get("total_price", 0.0)
		path_repr = " -> ".join(path)
		print(f"{index}. {path_repr} | {metric_label}: {metric_value} | total: R$ {total_price:.2f}")

		legs = route.get("legs", [])
		for leg in legs:
			print(f"   - {leg.get('from')} -> {leg.get('to')}: R$ {float(leg.get('price', 0.0)):.2f}")

	limits = result.get("limits", {})
	if limits.get("truncated"):
		print(
			"Aviso: busca interrompida por limite de seguranca "
			f"({limits.get('expansions_used', 0)}/{limits.get('max_expansions', '-')})."
		)


def main() -> None:
	# Orquestra a interface do terminal.
	airports = load_airports(AIRPORTS_FILE)
	routes = load_routes(ROUTES_FILE)

	print("Sistema de rotas aereas")
	origin_airport = select_airport(airports, "Digite o aeroporto de origem: ")
	destination_airport = select_airport(airports, "Digite o aeroporto de destino: ")

	print(
		f"\nOrigem selecionada: {origin_airport.name} - {origin_airport.city} ({origin_airport.iata})"
	)
	print(
		f"Destino selecionado: {destination_airport.name} - {destination_airport.city} ({destination_airport.iata})"
	)

	fastest_route: dict[str, Any] | None = None
	cheapest_path: dict[str, Any] | None = None

	try:
		fastest_route = bfs_min_connections(
			airports,
			routes,
			origin_airport.iata,
			destination_airport.iata,
		)
		print_ranked_routes(
			"Rotas com menos conexoes (top 3):",
			fastest_route,
			metric_key="connections",
			metric_label="conexoes",
		)

		if not fastest_route.get("found"):
			alternative_airport, alternative_result = find_first_working_alternative(
				airports=airports,
				routes=routes,
				origin_iata=origin_airport.iata,
				destination=destination_airport,
				solver=bfs_min_connections,
			)
			if alternative_airport and alternative_result:
				print(
					f"\nSem rota para {destination_airport.iata}. "
					f"Mostrando alternativa na mesma cidade: {alternative_airport.name} ({alternative_airport.iata})."
				)
				print_ranked_routes(
					"Rotas com menos conexoes (fallback):",
					alternative_result,
					metric_key="connections",
					metric_label="conexoes",
				)
	except NotImplementedError as error:
		print(f"\nBFS ainda nao disponivel: {error}")

	try:
		cheapest_route = price_formula (
			airports,
			routes,
			origin_airport.iata,
			destination_airport.iata,
		)
		print("\nPreco de voos diretos:")
		print(cheapest_route)
	except NotImplementedError as error:
		print(f"\nPreco ainda nao disponivel: {error}")

	try:
		cheapest_path = dijkstra (
			airports,
			routes,
			origin_airport.iata,
			destination_airport.iata,
		)
		print_ranked_routes(
			"Rotas mais baratas (Dijkstra, top 3):",
			cheapest_path,
			metric_key="segments",
			metric_label="trechos",
		)

		if not cheapest_path.get("found"):
			alternative_airport, alternative_result = find_first_working_alternative(
				airports=airports,
				routes=routes,
				origin_iata=origin_airport.iata,
				destination=destination_airport,
				solver=dijkstra,
			)
			if alternative_airport and alternative_result:
				print(
					f"\nSem rota para {destination_airport.iata}. "
					f"Mostrando alternativa na mesma cidade: {alternative_airport.name} ({alternative_airport.iata})."
				)
				print_ranked_routes(
					"Rotas mais baratas (Dijkstra, fallback):",
					alternative_result,
					metric_key="segments",
					metric_label="trechos",
				)
	except NotImplementedError as error:
		print(f"\nDijkstra ainda nao disponivel: {error}")


if __name__ == "__main__":
	main()
