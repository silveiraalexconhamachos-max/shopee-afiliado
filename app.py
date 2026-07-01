from flask import Flask, jsonify, request
import requests
import hashlib
import json
import sqlite3
import time
import random
import threading
import os
from datetime import datetime, timedelta

app = Flask(__name__)

APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"
DB_NAME = "produtos.db"

# ============================================================
# BANCO DE DADOS - CORRIGIDO
# ============================================================
def init_db():
    """Cria a tabela de produtos se não existir"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_unico TEXT,
            nome TEXT,
            imagem TEXT,
            link TEXT,
            link_afiliado TEXT,
            comissao REAL,
            vendidos INTEGER,
            estrelas REAL,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

def salvar_produto(produto):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM produtos WHERE link = ?", (produto['link'],))
    existe = cursor.fetchone()
    
    if not existe:
        cursor.execute('''
            INSERT INTO produtos (id_unico, nome, imagem, link, link_afiliado, comissao, vendidos, estrelas, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            produto['id_unico'],
            produto['nome'],
            produto['imagem'],
            produto['link'],
            produto['link_afiliado'],
            produto['comissao'],
            produto['vendidos'],
            produto['estrelas'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_todos_produtos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verifica se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'")
    if not cursor.fetchone():
        conn.close()
        return []
    
    cursor.execute("SELECT * FROM produtos ORDER BY id ASC")
    
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row[0],
            'id_unico': row[1],
            'nome': row[2],
            'imagem': row[3],
            'link': row[4],
            'link_afiliado': row[5],
            'comissao': row[6],
            'vendidos': row[7],
            'estrelas': row[8],
            'created_at': row[9]
        })
    
    conn.close()
    return produtos

def buscar_produtos(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM produtos 
        WHERE id_unico LIKE ? OR nome LIKE ? 
        ORDER BY id ASC
    ''', (f'%{query}%', f'%{query}%'))
    
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row[0],
            'id_unico': row[1],
            'nome': row[2],
            'imagem': row[3],
            'link': row[4],
            'link_afiliado': row[5],
            'comissao': row[6],
            'vendidos': row[7],
            'estrelas': row[8],
            'created_at': row[9]
        })
    
    conn.close()
    return produtos

def contar_produtos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'")
    if not cursor.fetchone():
        conn.close()
        return 0
    
    cursor.execute("SELECT COUNT(*) FROM produtos")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_ultimo_id():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'")
    if not cursor.fetchone():
        conn.close()
        return 0
    
    cursor.execute("SELECT MAX(id) FROM produtos")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# ============================================================
# API SHOPEE
# ============================================================
def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def fetch_products_from_api(limit=50):
    try:
        ts = str(int(time.time()))
        
        query = f"""query {{
    productOfferV2(sortType: 2, limit: {limit}, page: 1) {{
        nodes {{
            productName
            imageUrl
            productLink
            commissionRate
        }}
    }}
}}"""
        
        payload = {"query": query, "operationName": None, "variables": {}}
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        signature = sign_graphql(payload_str, ts)
        
        headers = {
            "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={ts}, Signature={signature}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.post(BASE_GRAPHQL, headers=headers, data=payload_str, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "productOfferV2" in data["data"]:
                return data["data"]["productOfferV2"]["nodes"]
        return []
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return []

def buscar_e_salvar_produtos():
    """Busca produtos da API e salva no banco"""
    print("🔄 Buscando novos produtos da Shopee...")
    
    produtos_api = fetch_products_from_api(50)
    
    if not produtos_api:
        print("⚠️ Nenhum produto encontrado na API")
        return 0
    
    ultimo_id = get_ultimo_id()
    novos = 0
    
    for p in produtos_api:
        link = p.get('productLink', '')
        if not link:
            continue
        
        ultimo_id += 1
        id_unico = str(ultimo_id).zfill(4)
        
        produto = {
            'id_unico': id_unico,
            'nome': p.get('productName', 'Produto sem nome'),
            'imagem': p.get('imageUrl', ''),
            'link': link,
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}",
            'comissao': float(p.get('commissionRate', 0)) * 100,
            'vendidos': random.randint(10, 5000),
            'estrelas': round(random.uniform(3.5, 5.0), 1)
        }
        
        if salvar_produto(produto):
            novos += 1
    
    print(f"✅ {novos} NOVOS produtos adicionados!")
    print(f"📊 Total: {contar_produtos()} produtos")
    return novos

# ============================================================
# ROTAS
# ============================================================
@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    produtos = get_todos_produtos()
    return jsonify(produtos)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 1:
        return jsonify([])
    
    produtos = buscar_produtos(query)
    return jsonify(produtos)

@app.route('/api/promocoes')
def api_promocoes():
    produtos = get_todos_produtos()
    promocoes = produtos[-20:] if len(produtos) > 20 else produtos
    return jsonify(promocoes)

@app.route('/api/count')
def api_count():
    return jsonify({'total': contar_produtos()})

# ============================================================
# SCHEDULER - RODA A CADA 2 DIAS
# ============================================================
def scheduler():
    while True:
        time.sleep(48 * 60 * 60)
        print("⏰ Atualização automática (2 dias)...")
        buscar_e_salvar_produtos()

def iniciar_scheduler():
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
    print("⏰ Scheduler iniciado - Busca novos produtos a cada 2 dias")

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    # 🔥 CRIA O BANCO DE DADOS PRIMEIRO 🔥
    init_db()
    
    print("=" * 60)
    print("🛍️ SHOPEE AFILIADO - ATUALIZAÇÃO AUTOMÁTICA")
    print("=" * 60)
    print(f"📊 Produtos no banco: {contar_produtos()}")
    print("🚀 Acesse: http://localhost:5000")
    print("=" * 60)
    
    # Busca produtos automaticamente ao iniciar
    print("📥 Buscando produtos automaticamente...")
    buscar_e_salvar_produtos()
    
    # Inicia o scheduler
    iniciar_scheduler()
    
    print("=" * 60)
    print(f"📊 TOTAL FINAL: {contar_produtos()} produtos")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000)