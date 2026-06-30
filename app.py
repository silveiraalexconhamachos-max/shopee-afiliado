from flask import Flask, jsonify, request
import requests
import hashlib
import json
from datetime import datetime
import time
import random

app = Flask(__name__)

APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"

CATEGORIAS = {
    "todos": None,
    "moda": 1000,
    "esporte": 2000,
    "informatica": 3000,
    "eletronicos": 4000,
    "beleza": 5000,
    "casa": 6000
}

def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def fetch_products(categoria_id=None, limit=50):
    """Busca produtos REAIS da Shopee"""
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
        
        payload = {"query": query, "operationName": None, "variables": {}}
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        signature = sign_graphql(payload_str, ts)
        
        headers = {
            "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={ts}, Signature={signature}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(BASE_GRAPHQL, headers=headers, data=payload_str, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "productOfferV2" in data["data"]:
                return data["data"]["productOfferV2"]["nodes"]
        return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def get_products_by_category(categoria):
    categoria_id = CATEGORIAS.get(categoria)
    return fetch_products(categoria_id, limit=50)

def get_all_products():
    """Busca produtos de todas as categorias"""
    todos = []
    for cat, cat_id in CATEGORIAS.items():
        if cat != "todos":
            produtos = fetch_products(cat_id, limit=30)
            if produtos:
                todos.extend(produtos)
            time.sleep(0.3)
    return todos

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    categoria = request.args.get('categoria', 'todos')
    
    if categoria == 'todos':
        produtos = get_all_products()
    else:
        produtos = get_products_by_category(categoria)
    
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        preco = random.randint(29, 399)  # Preço aleatório para demonstração
        
        formatted.append({
            'nome': p.get('productName', 'Produto'),
            'img': p.get('imageUrl', ''),
            'preco': preco,
            'preco_formatado': f"R$ {preco:.2f}".replace('.', ','),
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'comissao': float(p.get('commissionRate', 0)) * 100,
            'rating': round(random.uniform(3.5, 5.0), 1),
            'avaliacoes': random.randint(10, 500),
            'desconto': random.randint(10, 40) if random.random() > 0.5 else 0
        })
    
    return jsonify(formatted[:100])

@app.route('/api/promocoes')
def api_promocoes():
    produtos = get_all_products()
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos[:20]:
        link = p.get('productLink', '')
        preco = random.randint(29, 399)
        
        formatted.append({
            'nome': p.get('productName', 'Produto'),
            'img': p.get('imageUrl', ''),
            'preco_formatado': f"R$ {preco:.2f}".replace('.', ','),
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'rating': round(random.uniform(3.5, 5.0), 1),
            'desconto': random.randint(15, 50)
        })
    
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = get_all_products()
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos:
        nome = p.get('productName', '').lower()
        if query.lower() in nome:
            link = p.get('productLink', '')
            preco = random.randint(29, 399)
            
            formatted.append({
                'nome': p.get('productName', ''),
                'img': p.get('imageUrl', ''),
                'preco_formatado': f"R$ {preco:.2f}".replace('.', ','),
                'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
                'rating': round(random.uniform(3.5, 5.0), 1)
            })
    
    return jsonify(formatted[:50])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)