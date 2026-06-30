from flask import Flask, jsonify, request
import requests
import hashlib
import json
from datetime import datetime

app = Flask(__name__)

# ========== CREDENCIAIS CORRETAS ==========
APP_ID = "18340080482"
PASSWORD = "RPI4RF7PBYB6XJKNWTCFPPAQIQII2W32"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"

def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def fetch_products():
    """Busca produtos REAIS da Shopee"""
    try:
        ts = str(int(datetime.now().timestamp()))
        
        query = """query {
    productOfferV2(sortType: 2, limit: 50, page: 1) {
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {data}")
            
            if "data" in data and "productOfferV2" in data["data"]:
                nodes = data["data"]["productOfferV2"]["nodes"]
                print(f"✅ Encontrados: {len(nodes)} produtos REAIS")
                return nodes
            elif "errors" in data:
                print(f"❌ Erro: {data['errors']}")
                return []
        return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def get_fallback_products():
    """Produtos de exemplo (emergência)"""
    return [
        {
            "productName": "Smartphone Samsung Galaxy S24 Ultra 256GB",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_1234567-MLU123456789_012024-F.webp",
            "productLink": "https://shopee.com.br/product/123456789/",
            "commissionRate": 0.05
        }
    ]

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    # Tenta buscar produtos REAIS da Shopee
    produtos = fetch_products()
    
    # Se não encontrou, usa fallback
    if not produtos:
        print("⚠️ Usando produtos de fallback")
        produtos = get_fallback_products()
    
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        nome = p.get('productName', 'Produto sem nome')
        img = p.get('imageUrl', '')
        comissao = float(p.get('commissionRate', 0)) * 100
        
        if not img:
            img = 'https://via.placeholder.com/300x300/ee4d2d/ffffff?text=Produto'
        
        # Link de afiliado com seu APP_ID
        if link and link != '#':
            if '?' in link:
                link_afiliado = f"{link}&mmp_pid=an_{APP_ID}"
            else:
                link_afiliado = f"{link}?mmp_pid=an_{APP_ID}"
        else:
            link_afiliado = '#'
        
        formatted.append({
            'nome': nome,
            'img': img,
            'link_afiliado': link_afiliado,
            'comissao': comissao
        })
    
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = fetch_products()
    if not produtos:
        produtos = get_fallback_products()
    
    formatted = []
    for p in produtos:
        nome = p.get('productName', '').lower()
        if query.lower() in nome:
            link = p.get('productLink', '')
            img = p.get('imageUrl', '')
            if not img:
                img = 'https://via.placeholder.com/300x300/ee4d2d/ffffff?text=Produto'
            
            if link and link != '#':
                if '?' in link:
                    link_afiliado = f"{link}&mmp_pid=an_{APP_ID}"
                else:
                    link_afiliado = f"{link}?mmp_pid=an_{APP_ID}"
            else:
                link_afiliado = '#'
            
            formatted.append({
                'nome': p.get('productName', ''),
                'img': img,
                'link_afiliado': link_afiliado,
                'comissao': float(p.get('commissionRate', 0)) * 100
            })
    
    return jsonify(formatted[:30])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)