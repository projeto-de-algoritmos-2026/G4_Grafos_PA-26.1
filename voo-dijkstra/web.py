from flask import Flask, request, jsonify, render_template

import bfs
import price
import dijkstra
from main import load_airports, load_routes, AIRPORTS_FILE, ROUTES_FILE

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

if __name__ == '__main__':
    print("Iniciando servidor web...")
    print("Por favor, abra o navegador e acesse: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)