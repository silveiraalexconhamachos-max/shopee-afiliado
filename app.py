from flask import Flask, jsonify, request
import requests
import hashlib
import json
from datetime import datetime
import time

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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Produtos encontrados: {len(data.get('data', {}).get('productOfferV2', {}).get('nodes', []))}")
            if "data" in data and "productOfferV2" in data["data"]:
                return data["data"]["productOfferV2"]["nodes"]
        return []
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return []

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    categoria = request.args.get('categoria', 'todos')
    
    if categoria == 'todos':
        produtos = fetch_products(None, 50)
    else:
        categoria_id = CATEGORIAS.get(categoria)
        produtos = fetch_products(categoria_id, 50)
    
    # SE NÃO TEM PRODUTOS, RETORNA VAZIO (SEM FALLBACK)
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        nome = p.get('productName', 'Produto sem nome')
        img = p.get('imageUrl', '')
        comissao = float(p.get('commissionRate', 0)) * 100
        
        formatted.append({
            'nome': nome,
            'img': img,
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'comissao': comissao,
            'preco': '0.00',  # Será atualizado depois
            'preco_formatado': 'R$ 0,00',
            'rating': 0,
            'desconto': 0
        })
    
    return jsonify(formatted)

@app.route('/api/promocoes')
def api_promocoes():
    produtos = fetch_products(None, 30)
    
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos[:20]:
        link = p.get('productLink', '')
        formatted.append({
            'nome': p.get('productName', 'Produto'),
            'img': p.get('imageUrl', ''),
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'preco_formatado': 'R$ 0,00',
            'rating': 0,
            'desconto': 0
        })
    
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = fetch_products(None, 50)
    if not produtos:
        return jsonify([])
    
    formatted = []
    for p in produtos:
        nome = p.get('productName', '').lower()
        if query.lower() in nome:
            link = p.get('productLink', '')
            formatted.append({
                'nome': p.get('productName', ''),
                'img': p.get('imageUrl', ''),
                'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
                'preco_formatado': 'R$ 0,00',
                'rating': 0
            })
    
    return jsonify(formatted[:50])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)