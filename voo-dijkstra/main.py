from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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
	matches: list[Airport] = []

	for airport in airports:
		if upper_query and airport.iata.upper() == upper_query:
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

	try:
		fastest_route = bfs_min_connections(
			airports,
			routes,
			origin_airport.iata,
			destination_airport.iata,
		)
		print("\nRotas com menos conexoes:")
		print(fastest_route)
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
		print("\nResultado do Dijkstra:")
		print(cheapest_path)
	except NotImplementedError as error:
		print(f"\nDijkstra ainda nao disponivel: {error}")


if __name__ == "__main__":
	main()
