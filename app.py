from flask import Flask, jsonify, request
import requests
import hashlib
import json
import sqlite3
import time
import os
from datetime import datetime

app = Flask(__name__)

APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"
DB_NAME = "produtos.db"

CATEGORIAS = {
    "todos": None,
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
    """Cria a tabela de produtos se não existir"""
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
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

def salvar_produto(produto, categoria):
    """Salva um produto no banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    produto_id = produto.get('id')
    nome = produto.get('nome', 'Produto sem nome')
    imagem = produto.get('imagem', '')
    link = produto.get('link', '')
    link_afiliado = produto.get('link_afiliado', '')
    comissao = produto.get('comissao', 0)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Verifica se o produto já existe
    cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,))
    existe = cursor.fetchone()
    
    if existe:
        # Atualiza o produto existente
        cursor.execute('''
            UPDATE produtos 
            SET nome = ?, imagem = ?, link = ?, link_afiliado = ?, comissao = ?, updated_at = ?
            WHERE id = ?
        ''', (nome, imagem, link, link_afiliado, comissao, now, produto_id))
    else:
        # Insere novo produto
        cursor.execute('''
            INSERT INTO produtos (id, nome, imagem, link, link_afiliado, comissao, categoria, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (produto_id, nome, imagem, link, link_afiliado, comissao, categoria, now, now))
    
    conn.commit()
    conn.close()

def get_produtos_por_categoria(categoria):
    """Busca produtos do banco por categoria"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if categoria == 'todos' or categoria is None:
        cursor.execute('''
            SELECT * FROM produtos ORDER BY created_at DESC
        ''')
    else:
        cursor.execute('''
            SELECT * FROM produtos WHERE categoria = ? ORDER BY created_at DESC
        ''', (categoria,))
    
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
            'created_at': row[7],
            'updated_at': row[8]
        })
    
    conn.close()
    return produtos

def buscar_produtos_no_banco(query):
    """Busca produtos por nome no banco"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM produtos 
        WHERE nome LIKE ? 
        ORDER BY created_at DESC
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
            'created_at': row[7],
            'updated_at': row[8]
        })
    
    conn.close()
    return produtos

def contar_produtos():
    """Conta quantos produtos estão salvos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ============================================================
# FUNÇÕES DA API SHOPEE
# ============================================================
def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def fetch_products_from_api(categoria_id=None, limit=50):
    """Busca produtos da API Shopee"""
    try:
        ts = str(int(time.time()))
        
        query = f"""query {{
    productOfferV2(sortType: 2, limit: {limit}, page: 1"""
        
        if categoria_id:
            query += f", categoryId: {categoria_id}"
        
        query += """) {
        nodes {
            productName
            imageUrl
            productLink
            commissionRate
        }
    }
}"""
        
        payload = {
            "query": query,
            "operationName": None,
            "variables": {}
        }
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
# ROTAS FLASK
# ============================================================
@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/update-products', methods=['POST'])
def update_products():
    """Busca novos produtos da API e SALVA no banco"""
    print("🔄 Buscando novos produtos da Shopee...")
    
    total_novos = 0
    total_existentes = 0
    
    for categoria_nome, categoria_id in CATEGORIAS.items():
        if categoria_nome == 'todos':
            continue
        
        print(f"📥 Buscando produtos da categoria: {categoria_nome}")
        produtos = fetch_products_from_api(categoria_id, 30)
        
        if not produtos:
            print(f"⚠️ Nenhum produto encontrado para {categoria_nome}")
            continue
        
        for p in produtos:
            link = p.get('productLink', '')
            if not link:
                continue
            
            produto_id = hashlib.md5(link.encode()).hexdigest()[:12]
            link_afiliado = f"{link}?mmp_pid=an_{APP_ID}"
            nome = p.get('productName', 'Produto sem nome')
            imagem = p.get('imageUrl', '')
            comissao = float(p.get('commissionRate', 0)) * 100
            
            # Verifica se já existe
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,))
            existe = cursor.fetchone()
            conn.close()
            
            if existe:
                total_existentes += 1
            else:
                total_novos += 1
            
            produto = {
                'id': produto_id,
                'nome': nome,
                'imagem': imagem,
                'link': link,
                'link_afiliado': link_afiliado,
                'comissao': comissao
            }
            salvar_produto(produto, categoria_nome)
        
        time.sleep(0.5)  # Pausa para não sobrecarregar a API
    
    total = contar_produtos()
    print(f"✅ {total_novos} NOVOS produtos adicionados!")
    print(f"📊 Total de produtos no banco: {total}")
    
    return jsonify({
        'success': True,
        'novos': total_novos,
        'existentes': total_existentes,
        'total': total
    })

@app.route('/api/products')
def api_products():
    """Retorna produtos do banco de dados"""
    categoria = request.args.get('categoria', 'todos')
    produtos = get_produtos_por_categoria(categoria)
    
    # Formatar para o frontend
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
    """Busca produtos por nome no banco"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = buscar_produtos_no_banco(query)
    
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
    """Retorna total de produtos no banco"""
    return jsonify({'total': contar_produtos()})

if __name__ == '__main__':
    # Inicializa o banco de dados
    init_db()
    
    print("=" * 60)
    print("🛍️ SHOPEE AFILIADO - COM BANCO DE DADOS")
    print("=" * 60)
    print(f"📊 Produtos no banco: {contar_produtos()}")
    print("🚀 Acesse: http://localhost:5000")
    print("=" * 60)
    print("\n📌 COMANDOS:")
    print("  - POST /api/update-products  -> Busca novos produtos da API")
    print("  - GET /api/products          -> Lista produtos do banco")
    print("  - GET /api/search?q=termo    -> Busca produtos por nome")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000)