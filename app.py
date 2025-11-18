from flask import Flask, request, jsonify, render_template
import time
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz

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

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = "sqlite:///local_db.sqlite"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

FALL_DATA_TREE = BinarySearchTree() 

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
    """Endpoint para o ESP32 enviar dados."""
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

        novo_evento_db = Evento(
            timestamp=timestamp_key,
            tipo=event_type,
            lat=latitude,
            lon=longitude,
            acel=aceleracao
        )
        db.session.add(novo_evento_db)
        db.session.commit()
        
        FALL_DATA_TREE.insert(timestamp_key, payload)
        
        print(f"Evento armazenado (DB e ABB): Tipo={event_type}, Chave={timestamp_key}")
        
        return jsonify({"status": "sucesso", "chave_registro": timestamp_key}), 200

    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao processar requisição: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500

@app.route('/api/eventos', methods=['GET'])
def get_events():
    """Endpoint para o dashboard (lê da Árvore/cache)."""
    events = FALL_DATA_TREE.get_all_events_sorted()
    return jsonify(eventos=events, total=len(events)), 200

# ------------------------------------------------------------------
# --- INÍCIO DAS NOVAS ROTAS (PÁGINA DE DADOS E "IA") ---
# ------------------------------------------------------------------

@app.route('/dados')
def pagina_dados():
    """Serve a nova página HTML de análise de dados."""
    return render_template('dados.html')

@app.route('/api/analise_de_risco', methods=['GET'])
def analise_de_risco():
    """
    Este é o nosso "Algoritmo de IA".
    Ele lê do Banco de Dados e aplica regras de heurística.
    """
    print("Iniciando análise de risco algorítmica...")
    try:
        fuso_horario_br = pytz.timezone('America/Sao_Paulo')
        
        HORA_INICIO_NOITE = 22
        HORA_FIM_NOITE = 6
        
        agora = datetime.now(fuso_horario_br)
        uma_semana_atras = agora - timedelta(days=7)
        timestamp_uma_semana_atras = int(uma_semana_atras.timestamp())

        eventos_do_db = Evento.query.all()
        
        if not eventos_do_db:
            return jsonify({"alertas": ["Não há dados suficientes para análise."]})

        total_eventos = len(eventos_do_db)
        eventos_noturnos = 0
        eventos_recentes = 0
        total_quedas = 0
        total_panicos = 0

        for evento in eventos_do_db:
            ts_evento = datetime.fromtimestamp(evento.timestamp, fuso_horario_br)
            
            if ts_evento.hour >= HORA_INICIO_NOITE or ts_evento.hour < HORA_FIM_NOITE:
                eventos_noturnos += 1
            
            if evento.timestamp >= timestamp_uma_semana_atras:
                eventos_recentes += 1
            
            if evento.tipo == 'queda':
                total_quedas += 1
            elif evento.tipo == 'panico':
                total_panicos += 1

        lista_de_alertas = []

        if eventos_noturnos > 0:
            alerta = (
                f"Detectamos {eventos_noturnos} evento(s) "
                f"ocorrendo durante a noite (22h-06h). "
                "Isso pode indicar confusão noturna (sundowning) ou risco de queda no escuro."
            )
            lista_de_alertas.append({"nivel": "alto", "texto": alerta})
        
        if eventos_recentes > 2:
            alerta = (
                f"A frequência de eventos aumentou, "
                f"com {eventos_recentes} alertas registrados apenas nos últimos 7 dias. "
                "Recomenda-se observação."
            )
            lista_de_alertas.append({"nivel": "medio", "texto": alerta})
        elif eventos_recentes > 0:
            alerta = (
                f"{eventos_recentes} evento(s) "
                f"registrado(s) nos últimos 7 dias."
            )
            lista_de_alertas.append({"nivel": "info", "texto": alerta})

        if total_quedas > total_panicos and total_quedas > 0:
            alerta = (
                f"O paciente registrou mais quedas ({total_quedas}) "
                f"do que botões de pânico ({total_panicos}). "
                "Isso pode indicar uma dificuldade de locomoção."
            )
            lista_de_alertas.append({"nivel": "info", "texto": alerta})

        if not lista_de_alertas:
            lista_de_alertas.append({
                "nivel": "info", 
                "texto": "Nenhum padrão de risco óbvio detectado nos dados atuais. Continue monitorando."
            })
        
        print(f"✅ Análise de risco concluída. {len(lista_de_alertas)} alertas gerados.")
        return jsonify(alertas=lista_de_alertas)

    except Exception as e:
        print(f"Erro na análise de risco: {e}")
        return jsonify({"erro": str(e)}), 500

# ------------------------------------------------------------------
# PARTE 4: Inicialização do Servidor
# ------------------------------------------------------------------

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
            payload = {"tipo": evento.tipo, "lat": evento.lat, "lon": evento.lon, "acel": evento.acel}
            FALL_DATA_TREE.insert(evento.timestamp, payload)
            
        print(f"{len(eventos_do_db)} eventos carregados do DB para a memória.")
    
    except Exception as e:
        print(f"Erro ao carregar dados do DB: {e}")
        print("Continuando com a árvore vazia...")
    
    print("-----------------------------------------------------")
    print("  SERVIÇO INICIADO (Modo Híbrido) - Aguardando Conexões ")
    print("-----------------------------------------------------")


with app.app_context():
    carregar_db_para_abb()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)