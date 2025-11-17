from flask import Flask, request, jsonify, render_template
import time
import os

# ------------------------------------------------------------------
# PARTE 1: Lógica da Árvore Binária de Busca (BST)
# ------------------------------------------------------------------

class Node:
    """Representa um nó na Árvore Binária de Busca."""
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.left = None
        self.right = None

class BinarySearchTree:
    """Implementa a lógica da Árvore Binária de Busca (ABB)."""
    def __init__(self):
        self.root = None

    def insert(self, key, data):
        """Insere um novo evento na ABB com base no timestamp (key)."""
        if self.root is None:
            self.root = Node(key, data)
        else:
            self._insert_recursive(self.root, key, data)

    def _insert_recursive(self, node, key, data):
        """Função auxiliar recursiva para inserção."""
        # Se a nova chave for menor que a chave do nó atual, navega para a esquerda
        if key < node.key:
            if node.left is None:
                node.left = Node(key, data)
            else:
                self._insert_recursive(node.left, key, data)
        # Se a nova chave for maior que a chave do nó atual, navega para a direita
        elif key > node.key:
            if node.right is None:
                node.right = Node(key, data)
            else:
                self._insert_recursive(node.right, key, data)

    def inorder_traversal(self, node):
        """Percorre a árvore em ordem (Inorder) para retornar os eventos."""
        res = []
        if node:
            # 1. Esquerda (eventos mais antigos)
            res.extend(self.inorder_traversal(node.left))
            
            # 2. Raiz (evento atual)
            res.append({"key": node.key, "data": node.data})
            
            # 3. Direita (eventos mais recentes)
            res.extend(self.inorder_traversal(node.right))
        return res

    def get_all_events_sorted(self):
        """Função wrapper para obter todos os eventos ordenados."""
        return self.inorder_traversal(self.root)

# ------------------------------------------------------------------
# PARTE 2: Webservice Flask
# ------------------------------------------------------------------

# Configurando o Flask
app = Flask(__name__)
FALL_DATA_TREE = BinarySearchTree() # Instância global da ABB

# Rota principal que carrega a interface HTML
@app.route('/')
def index():
    """Serve a página HTML do monitor."""
    # O Flask procura automaticamente monitor.html na pasta 'templates'
    return render_template('monitor.html')

# Rota para receber dados do ESP32 (POST)
@app.route('/api/reportar_evento', methods=['POST'])
def report_event():
    """Endpoint para o ESP32 enviar dados de queda ou pânico."""
    try:
        data = request.get_json() 
        if data is None:
            return jsonify({"status": "erro", "mensagem": "JSON inválido ou ausente"}), 400
        
        event_type = data.get('tipo_evento')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        aceleracao = data.get('aceleracao', 'N/A')
        
        if not all([event_type, latitude, longitude]):
            return jsonify({"status": "erro", "mensagem": "Dados incompletos (tipo, lat, ou lon)"}), 400

        timestamp_key = int(time.time()) 
        
        payload = {
            "tipo": event_type,
            "lat": latitude,
            "lon": longitude,
            "acel": aceleracao
        }

        # Armazenamento na Árvore Binária de Busca
        FALL_DATA_TREE.insert(timestamp_key, payload)
        
        print(f"✅ Evento armazenado: Tipo={event_type}, Chave={timestamp_key}")
        
        return jsonify({"status": "sucesso", "chave_registro": timestamp_key}), 200

    except Exception as e:
        print(f"❌ Erro ao processar requisição: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500

# Rota para visualizar todos os eventos (GET)
@app.route('/api/eventos', methods=['GET'])
def get_events():
    """Endpoint para retornar todos os eventos em ordem cronológica (via ABB)."""
    events = FALL_DATA_TREE.get_all_events_sorted()
    return jsonify(eventos=events, total=len(events)), 200

if __name__ == '__main__':
    # Esta verificação garante que a pasta 'templates' existe antes de iniciar o servidor
    if not os.path.exists('templates'):
        os.makedirs('templates')

    print("-----------------------------------------------------")
    print("  SERVIÇO INICIADO - Aguardando Conexões do ESP32 ")
    print("-----------------------------------------------------")
    
    # ALTERAÇÃO AQUI: Porta padrão alterada para 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
