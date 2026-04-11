from flask import Flask, request, jsonify, render_template

import bfs
import price
import dijkstra
from main import AIRPORTS_FILE, ROUTES_FILE, airport_matches, load_airports, load_routes

app = Flask(__name__)

# Carrega os dados na inicialização para não precisar ler o arquivo a cada requisição
print("Carregando aeroportos e rotas, aguarde...")
airports = load_airports(AIRPORTS_FILE)
routes = load_routes(ROUTES_FILE)
print("Dados carregados com sucesso!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/rotas')
def api_rotas():
    # Recebe os parâmetros JS e envia para as suas funções
    origem = request.args.get('origem', '').strip().upper()
    destino = request.args.get('destino', '').strip().upper()
    
    if not origem or not destino:
        return jsonify({"erro": "Parâmetros 'origem' e 'destino' são obrigatórios."}), 400
        
    try:
        bfs_result = bfs.find_route_with_fewest_connections(airports, routes, origem, destino)
        price_result = price.calculate_price(airports, routes, origem, destino)
        dijkstra_result = dijkstra.find_shortest_route(airports, routes, origem, destino)
        
        return jsonify({
            "bfs": bfs_result,
            "direto": price_result,
            "dijkstra": dijkstra_result
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/aeroportos')
def api_aeroportos():
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify([])

    matches = airport_matches(airports, query)[:10]
    return jsonify([
        {
            "iata": airport.iata,
            "icao": airport.icao,
            "name": airport.name,
            "city": airport.city,
            "country": airport.country,
            "label": f"{airport.city} - {airport.name} ({airport.iata})",
        }
        for airport in matches
    ])

if __name__ == '__main__':
    print("Iniciando servidor web...")
    print("Por favor, abra o navegador e acesse: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)