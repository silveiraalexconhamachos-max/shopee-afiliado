from flask import Flask, jsonify, request
import requests
import hashlib
import json
from datetime import datetime

app = Flask(__name__)

APP_ID = "18340080482"
PASSWORD = "54YZZLO55TDZ4WU6CF74PSSGY6U722PI"
BASE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"

def sign_graphql(payload_str, ts):
    msg = f"{APP_ID}{ts}{payload_str}{PASSWORD}"
    return hashlib.sha256(msg.encode()).hexdigest()

def get_fallback_products():
    """Produtos de exemplo para quando a API não funcionar"""
    return [
        {
            "productName": "Smartphone Samsung Galaxy S24 Ultra 256GB",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_1234567-MLU123456789_012024-F.webp",
            "productLink": "https://shopee.com.br/product/123456789/",
            "commissionRate": 0.05
        },
        {
            "productName": "Fone de Ouvido Bluetooth JBL Tune 510BT Preto",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_9876543-MLU987654321_012024-F.webp",
            "productLink": "https://shopee.com.br/product/987654321/",
            "commissionRate": 0.04
        },
        {
            "productName": "Notebook Dell Inspiron 15 3000 8GB RAM 256GB SSD",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_4567891-MLU456789123_012024-F.webp",
            "productLink": "https://shopee.com.br/product/456789123/",
            "commissionRate": 0.06
        },
        {
            "productName": "Smart TV LG 50 Polegadas 4K UHD WebOS",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_7894561-MLU789456123_012024-F.webp",
            "productLink": "https://shopee.com.br/product/789456123/",
            "commissionRate": 0.04
        },
        {
            "productName": "PlayStation 5 Slim Digital 825GB Branco",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_3216549-MLU321654987_012024-F.webp",
            "productLink": "https://shopee.com.br/product/321654987/",
            "commissionRate": 0.03
        },
        {
            "productName": "Smartwatch Samsung Galaxy Watch 6 40mm",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_6543219-MLU654321987_012024-F.webp",
            "productLink": "https://shopee.com.br/product/654321987/",
            "commissionRate": 0.04
        },
        {
            "productName": "Fritadeira Elétrica Sem Óleo Air Fryer 3,5L",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_1472583-MLU147258369_012024-F.webp",
            "productLink": "https://shopee.com.br/product/147258369/",
            "commissionRate": 0.05
        },
        {
            "productName": "Carregador Portátil Power Bank 20000mAh",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_2581473-MLU258147369_012024-F.webp",
            "productLink": "https://shopee.com.br/product/258147369/",
            "commissionRate": 0.03
        },
        {
            "productName": "Mouse Gamer RGB 1600DPI - Preto",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_3692581-MLU369258147_012024-F.webp",
            "productLink": "https://shopee.com.br/product/369258147/",
            "commissionRate": 0.03
        },
        {
            "productName": "Cadeira Gamer Reclinável - Vermelha",
            "imageUrl": "https://http2.mlstatic.com/D_NQ_NP_2X_7418529-MLU741852963_012024-F.webp",
            "productLink": "https://shopee.com.br/product/741852963/",
            "commissionRate": 0.05
        }
    ]

def fetch_products():
    try:
        ts = str(int(datetime.now().timestamp()))
        
        query = """query {
    productOfferV2(sortType: 2, limit: 30, page: 1) {
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
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Origin": "https://shopee.com.br",
            "Referer": "https://shopee.com.br/"
        }
        
        response = requests.post(BASE_GRAPHQL, headers=headers, data=payload_str, timeout=15)
        
        # Log para debug
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {data}")
            if "data" in data and "productOfferV2" in data["data"]:
                nodes = data["data"]["productOfferV2"]["nodes"]
                print(f"Encontrados: {len(nodes)} produtos")
                return nodes
        return []
    except Exception as e:
        print(f"Erro na API: {e}")
        return []

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/products')
def api_products():
    produtos = fetch_products()
    
    # Se não encontrou produtos, usa fallback
    if not produtos:
        print("⚠️ Usando produtos de fallback")
        produtos = get_fallback_products()
    
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        nome = p.get('productName', 'Produto sem nome')
        img = p.get('imageUrl', '')
        
        if not img or img == '':
            img = 'https://via.placeholder.com/300x300/ee4d2d/ffffff?text=Produto'
        
        # Corrigir link de afiliado
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
            'comissao': float(p.get('commissionRate', 0)) * 100
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