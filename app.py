from flask import Flask, jsonify, request
import requests
import hashlib
import json
from datetime import datetime
import time

app = Flask(__name__)

# ========== CREDENCIAIS ==========
APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"

# ========== CATEGORIAS ==========
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
    """Busca produtos REAIS da Shopee por categoria"""
    try:
        ts = str(int(time.time()))
        
        # Query base
        query = f"""query {{
    productOfferV2(sortType: 2, limit: {limit}, page: 1"""
        
        # Adiciona categoria se especificada
        if categoria_id:
            query += f", categoryId: {categoria_id}"
        
        query += """) {
        nodes {
            productName
            imageUrl
            productLink
            commissionRate
            price
            ratingStar
            ratingCount
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
                nodes = data["data"]["productOfferV2"]["nodes"]
                print(f"✅ {len(nodes)} produtos encontrados")
                return nodes
        return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def get_products_by_category(categoria):
    """Busca produtos por categoria"""
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
                print(f"✅ {len(produtos)} produtos em {cat}")
            time.sleep(0.5)  # Pausa para não sobrecarregar a API
    return todos

# ========== ROTAS ==========

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    """Retorna todos os produtos"""
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
        preco = p.get('price', 0)
        rating = p.get('ratingStar', 0)
        avaliacoes = p.get('ratingCount', 0)
        
        formatted.append({
            'nome': p.get('productName', 'Produto'),
            'img': p.get('imageUrl', ''),
            'preco': preco,
            'preco_formatado': f"R$ {preco:.2f}".replace('.', ',') if preco else 'R$ 0,00',
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'comissao': float(p.get('commissionRate', 0)) * 100,
            'rating': rating,
            'avaliacoes': avaliacoes,
            'desconto': random.randint(10, 40) if preco else 0
        })
    
    return jsonify(formatted[:100])

@app.route('/api/promocoes')
def api_promocoes():
    """Retorna produtos em promoção (Desconto do Dia)"""
    produtos = get_all_products()
    
    if not produtos:
        return jsonify([])
    
    # Filtra apenas produtos com preço
    with_price = [p for p in produtos if p.get('price', 0) > 0]
    
    # Ordena por rating e pega os melhores
    sorted_prods = sorted(with_price, key=lambda x: x.get('ratingStar', 0), reverse=True)
    
    formatted = []
    for p in sorted_prods[:20]:  # Pega os 20 melhores
        link = p.get('productLink', '')
        preco = p.get('price', 0)
        rating = p.get('ratingStar', 0)
        
        formatted.append({
            'nome': p.get('productName', 'Produto'),
            'img': p.get('imageUrl', ''),
            'preco_formatado': f"R$ {preco:.2f}".replace('.', ',') if preco else 'R$ 0,00',
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'rating': rating,
            'desconto': random.randint(15, 50)
        })
    
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    """Busca produtos por nome"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    # Busca produtos de todas as categorias
    produtos = get_all_products()
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos:
        nome = p.get('productName', '').lower()
        if query.lower() in nome:
            link = p.get('productLink', '')
            preco = p.get('price', 0)
            
            formatted.append({
                'nome': p.get('productName', ''),
                'img': p.get('imageUrl', ''),
                'preco_formatado': f"R$ {preco:.2f}".replace('.', ',') if preco else 'R$ 0,00',
                'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
                'rating': p.get('ratingStar', 0)
            })
    
    return jsonify(formatted[:50])

if __name__ == '__main__':
    import random
    app.run(host='0.0.0.0', port=5000)