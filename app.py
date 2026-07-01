from flask import Flask, jsonify, request
import requests
import hashlib
import json
import sqlite3
import time
import os
import threading
from datetime import datetime

app = Flask(__name__)

APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"
DB_NAME = "produtos.db"

CATEGORIAS = {
    "moda": 1000,
    "esporte": 2000,
    "informatica": 3000,
    "eletronicos": 4000,
    "beleza": 5000,
    "casa": 6000
}

# ============================================================
# BANCO DE DADOS
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id TEXT PRIMARY KEY,
            nome TEXT,
            imagem TEXT,
            link TEXT,
            link_afiliado TEXT,
            comissao REAL,
            categoria TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

def salvar_produto(produto, categoria):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto['id'],))
    existe = cursor.fetchone()
    
    if not existe:
        cursor.execute('''
            INSERT INTO produtos (id, nome, imagem, link, link_afiliado, comissao, categoria, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            produto['id'],
            produto['nome'],
            produto['imagem'],
            produto['link'],
            produto['link_afiliado'],
            produto['comissao'],
            categoria,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    conn.commit()
    conn.close()

def get_produtos(categoria=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if categoria and categoria != 'todos':
        cursor.execute("SELECT * FROM produtos WHERE categoria = ? ORDER BY created_at DESC", (categoria,))
    else:
        cursor.execute("SELECT * FROM produtos ORDER BY created_at DESC")
    
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row[0],
            'nome': row[1],
            'imagem': row[2],
            'link': row[3],
            'link_afiliado': row[4],
            'comissao': row[5],
            'categoria': row[6],
            'created_at': row[7]
        })
    
    conn.close()
    return produtos

def buscar_produtos_por_nome(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM produtos WHERE nome LIKE ? ORDER BY created_at DESC
    ''', (f'%{query}%',))
    
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row[0],
            'nome': row[1],
            'imagem': row[2],
            'link': row[3],
            'link_afiliado': row[4],
            'comissao': row[5],
            'categoria': row[6],
            'created_at': row[7]
        })
    
    conn.close()
    return produtos

def contar_produtos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ============================================================
# API SHOPEE
# ============================================================
def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def fetch_products_from_api(categoria_id, limit=50):
    try:
        ts = str(int(time.time()))
        
        query = f"""query {{
    productOfferV2(sortType: 2, limit: {limit}, page: 1, categoryId: {categoria_id}) {{
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

# ============================================================
# CARREGAR PRODUTOS AUTOMATICAMENTE
# ============================================================
def carregar_produtos_automatico():
    """Função que roda em background e carrega produtos de todas as categorias"""
    print("🔄 Iniciando carga automática de produtos...")
    
    total_novos = 0
    
    for categoria_nome, categoria_id in CATEGORIAS.items():
        print(f"📥 Buscando produtos da categoria: {categoria_nome}")
        
        produtos = fetch_products_from_api(categoria_id, 30)
        
        if not produtos:
            print(f"⚠️ Nenhum produto para {categoria_nome}")
            continue
        
        for p in produtos:
            link = p.get('productLink', '')
            if not link:
                continue
            
            produto = {
                'id': hashlib.md5(link.encode()).hexdigest()[:12],
                'nome': p.get('productName', 'Produto sem nome'),
                'imagem': p.get('imageUrl', ''),
                'link': link,
                'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}",
                'comissao': float(p.get('commissionRate', 0)) * 100
            }
            
            salvar_produto(produto, categoria_nome)
            total_novos += 1
        
        print(f"✅ {len(produtos)} produtos da categoria {categoria_nome}")
        time.sleep(0.5)
    
    total = contar_produtos()
    print(f"🎯 TOTAL DE PRODUTOS CARREGADOS: {total}")

# ============================================================
# ROTAS
# ============================================================
@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    categoria = request.args.get('categoria', 'todos')
    produtos = get_produtos(categoria)
    
    formatted = []
    for p in produtos:
        formatted.append({
            'id': p['id'],
            'nome': p['nome'],
            'img': p['imagem'],
            'link_afiliado': p['link_afiliado'],
            'comissao': p['comissao'],
            'categoria': p['categoria']
        })
    
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = buscar_produtos_por_nome(query)
    
    formatted = []
    for p in produtos:
        formatted.append({
            'id': p['id'],
            'nome': p['nome'],
            'img': p['imagem'],
            'link_afiliado': p['link_afiliado'],
            'comissao': p['comissao'],
            'categoria': p['categoria']
        })
    
    return jsonify(formatted)

@app.route('/api/count')
def api_count():
    return jsonify({'total': contar_produtos()})

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    init_db()
    
    print("=" * 60)
    print("🛍️ SHOPEE AFILIADO - CARREGA AUTOMÁTICO")
    print("=" * 60)
    print("⏳ Carregando produtos da Shopee...")
    print("=" * 60)
    
    # CARREGA OS PRODUTOS AUTOMATICAMENTE
    carregar_produtos_automatico()
    
    print("=" * 60)
    print(f"📊 TOTAL DE PRODUTOS: {contar_produtos()}")
    print("🚀 Acesse: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000)