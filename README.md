# G4_Grafos_PA-26.1

## NomedoProjeto

Conteúdo da Disciplina: Grafos <br>

## Aluno
|Matrícula | Aluno |
| -- | -- |
| 23/1027032  | Arthur Evangelista de Oliveira |
| 23/1038303 | Yan Matheus Santa Brigida de Aguiar |

## Sobre 
Descreva os objetivos do seu projeto e como ele funciona. 

## Screenshots
Adicione 3 ou mais screenshots do projeto em funcionamento.

## Instalação 
Linguagem: **Python 3.10+**<br>
Framework (Web): **Flask**<br>

**Passo a passo de instalação no Windows:**

1. Clone o repositório ou navegue até a pasta do projeto:
   ```bash
   cd voo-dijkstra
   ```
2. (Recomendado) Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instale a biblioteca do servidor Web (Flask):
   ```bash
   pip install flask
   ```

## Uso 

Você pode executar o projeto de duas maneiras: Terminal (CLI) ou Interface Gráfica (Web).

### Opção 1: Via Terminal (CLI)
Essa opção busca os aeroportos digitando o IATA, o nome, a cidade ou o ICAO do aeroporto. No terminal, execute:
```bash
python main.py
```
Siga as instruções na tela listando a origem e destino desejados e o terminal irá imprimir o caminho com menos conexões (BFS), a cotação do voo direto e o voo mais barato (Dijkstra).

### Opção 2: Interface Gráfica (Aplicação Web)
Essa opção sobe um pequeno servidor local para visualizar a busca em uma bela página HTML:
```bash
python web.py
```
Após executar este comando:
1. Abra o seu navegador web (Chrome, Edge, Firefox, etc).
2. Acesse a URL: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**
3. Digite os códigos IATA (Ex: BSB, GRU) e clique em "Verificar Rotas".

## Outros 
Quaisquer outras informações sobre seu projeto podem ser descritas abaixo.