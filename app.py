from flask import Flask, request, jsonify, render_template
import time
import os
from flask_sqlalchemy import SQLAlchemy  # <-- NOVA IMPORTAÇÃO

# ------------------------------------------------------------------
# PARTE 1: Lógica da Árvore Binária de Busca (BST)
# (INTOCADA, COMO VOCÊ PEDIU)
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
        if key < node.key:
            if node.left is None:
                node.left = Node(key, data)
            else:
                self._insert_recursive(node.left, key, data)
        elif key > node.key:
            if node.right is None:
                node.right = Node(key, data)
            else:
                self._insert_recursive(node.right, key, data)

    def inorder_traversal(self, node):
        """Percorre a árvore em ordem (Inorder) para retornar os eventos."""
        res = []
        if node:
            res.extend(self.inorder_traversal(node.left))
            res.append({"key": node.key, "data": node.data})
            res.extend(self.inorder_traversal(node.right))
        return res

    def get_all_events_sorted(self):
        """Função wrapper para obter todos os eventos ordenados."""
        return self.inorder_traversal(self.root)

# ------------------------------------------------------------------
# PARTE 2: Webservice Flask E Configuração do Banco de Dados
# ------------------------------------------------------------------

app = Flask(__name__)

# --- CONFIGURAÇÃO DO BANCO DE DADOS (NOVA) ---
# Pega o URL do banco de dados que você configurou no Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Corrige o URL do Render de "postgres://" para "postgresql://"
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Se estiver rodando local, usa um arquivo de banco local
    DATABASE_URL = "sqlite:///local_db.sqlite"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# --- FIM DA CONFIGURAÇÃO DO DB ---


# Instância global da ABB (Nosso "cache" em memória)
FALL_DATA_TREE = BinarySearchTree() 


# --- MODELO DA TABELA DO BANCO DE DADOS (NOVO) ---
# Isso define como vamos salvar os dados no PostgreSQL
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger, nullable=False, index=True)
    tipo = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    acel = db.Column(db.String(50))

# ------------------------------------------------------------------
# PARTE 3: Rotas do Webservice
# ------------------------------------------------------------------

@app.route('/')
def index():
    """Serve a página HTML do monitor."""
    return render_template('monitor.html')

@app.route('/api/reportar_evento', methods=['POST'])
def report_event():
    """
    Endpoint para o ESP32 enviar dados.
    (MODIFICADO para salvar no DB e na ABB)
    """
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

        # --- MODIFICAÇÃO (SALVAR EM DOIS LUGARES) ---
        
        # 1. Armazenamento no Banco de Dados (Para persistência)
        novo_evento_db = Evento(
            timestamp=timestamp_key,
            tipo=event_type,
            lat=latitude,
            lon=longitude,
            acel=aceleracao
        )
        db.session.add(novo_evento_db)
        db.session.commit()
        
        # 2. Armazenamento na Árvore Binária (Para o cache)
        FALL_DATA_TREE.insert(timestamp_key, payload)
        
        # --- FIM DA MODIFICAÇÃO ---
        
        print(f"✅ Evento armazenado (DB e ABB): Tipo={event_type}, Chave={timestamp_key}")
        
        return jsonify({"status": "sucesso", "chave_registro": timestamp_key}), 200

    except Exception as e:
        db.session.rollback() # Desfaz a escrita no DB se algo der errado
        print(f"❌ Erro ao processar requisição: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500

@app.route('/api/eventos', methods=['GET'])
def get_events():
    """
    Endpoint para retornar todos os eventos.
    (INTOCADO - Continua lendo da Árvore em memória, que é rápido)
    """
    events = FALL_DATA_TREE.get_all_events_sorted()
    return jsonify(eventos=events, total=len(events)), 200

# ------------------------------------------------------------------
# PARTE 4: Inicialização do Servidor
# ------------------------------------------------------------------

# Esta função (NOVA) roda ANTES do servidor iniciar
# Ela "aquece o cache", lendo do DB e populando a Árvore
def carregar_db_para_abb():
    print("-----------------------------------------------------")
    print("Iniciando servidor...")
    print("Criando tabelas do banco de dados (se não existirem)...")
    db.create_all()
    
    print("Carregando eventos do Banco de Dados para a Árvore (ABB)...")
    try:
        eventos_do_db = Evento.query.order_by(Evento.timestamp).all()
        if not eventos_do_db:
            print("Nenhum evento anterior encontrado no DB.")
        
        for evento in eventos_do_db:
            # Recria o formato 'payload' que a Árvore espera
            payload = {
                "tipo": evento.tipo,
                "lat": evento.lat,
                "lon": evento.lon,
                "acel": evento.acel
            }
            # Insere na Árvore em memória
            FALL_DATA_TREE.insert(evento.timestamp, payload)
            
        print(f"✅ {len(eventos_do_db)} eventos carregados do DB para a memória.")
    
    except Exception as e:
        print(f"❌ Erro ao carregar dados do DB: {e}")
        print("Continuando com a árvore vazia...")
    
    print("-----------------------------------------------------")
    print("  SERVIÇO INICIADO (Modo Híbrido) - Aguardando Conexões ")
    print("-----------------------------------------------------")


# Bloco que roda o 'carregar_db_para_abb' ANTES de iniciar
with app.app_context():
    carregar_db_para_abb()

# Bloco para rodar localmente (python3 app.py)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)