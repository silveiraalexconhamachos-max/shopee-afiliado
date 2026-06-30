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

def fetch_products():
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
        data = response.json()
        
        if "data" in data and "productOfferV2" in data["data"]:
            return data["data"]["productOfferV2"]["nodes"]
        return []
    except Exception as e:
        print(f"Erro: {e}")
        return []

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛍️ Shopee Afiliado</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #ee4d2d, #ff6f3d); padding: 20px; color: white; text-align: center; }
            .header h1 { font-size: 2rem; }
            .header h1 span { color: #ffe066; }
            .header p { opacity: 0.8; margin-top: 5px; }
            .search { max-width: 500px; margin: 20px auto; display: flex; padding: 0 20px; }
            .search input { flex:1; padding:12px 18px; border:2px solid #ddd; border-radius:8px 0 0 8px; font-size:1rem; outline:none; }
            .search input:focus { border-color:#ee4d2d; }
            .search button { padding:12px 24px; background:#ee4d2d; color:white; border:none; border-radius:0 8px 8px 0; cursor:pointer; font-weight:600; transition:0.3s; }
            .search button:hover { background:#d43c1e; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .categorias { display: flex; gap: 10px; overflow-x: auto; padding: 10px 0; margin-bottom: 20px; flex-wrap: wrap; }
            .cat-btn { padding: 8px 20px; border: 2px solid #ddd; border-radius: 20px; background: white; cursor: pointer; white-space: nowrap; font-size: 0.9rem; transition:0.3s; }
            .cat-btn:hover { border-color: #ee4d2d; transform: scale(1.05); }
            .cat-btn.active { background: #ee4d2d; color: white; border-color: #ee4d2d; }
            .info-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; color: #666; font-size: 0.9rem; flex-wrap: wrap; gap: 10px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.08); transition: 0.3s; }
            .card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.12); }
            .card img { width: 100%; height: 200px; object-fit: cover; background: #f8f8f8; }
            .card .info { padding: 15px; }
            .card .nome { font-weight: 600; margin-bottom: 8px; height: 42px; overflow: hidden; font-size: 0.95rem; color: #333; }
            .card .preco { color: #ee4d2d; font-size: 1.2rem; font-weight: 700; margin-bottom: 12px; }
            .btn-buy { background: #ee4d2d; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 1rem; font-weight: 600; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px; }
            .btn-buy:hover { background: #d43c1e; transform: scale(1.02); }
            .loading { text-align: center; padding: 60px 20px; color: #666; grid-column: 1 / -1; }
            .loading i { font-size: 2.5rem; color: #ee4d2d; animation: spin 1s linear infinite; display: block; margin-bottom: 15px; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
            .no-results { text-align: center; padding: 60px 20px; color: #999; grid-column: 1 / -1; }
            .no-results i { font-size: 3rem; color: #ddd; margin-bottom: 15px; display: block; }
            .footer { text-align: center; padding: 20px; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 30px; }
            @media (max-width: 768px) {
                .grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
                .card img { height: 150px; }
                .categorias { flex-wrap: nowrap; }
                .header h1 { font-size: 1.5rem; }
                .search { padding: 0 10px; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛍️ Shopee<span>Afiliado</span></h1>
            <p>Ofertas com link de afiliado - Compre com segurança</p>
        </div>
        
        <div class="search">
            <input id="searchInput" placeholder="🔍 Buscar produtos..." onkeyup="buscar(event)">
            <button onclick="buscar()"><i class="fas fa-search"></i> Buscar</button>
        </div>
        
        <div class="container">
            <div class="categorias" id="categorias">
                <button class="cat-btn active" onclick="loadProducts('todos', this)">🛍️ Todos</button>
                <button class="cat-btn" onclick="loadProducts('moda', this)">👗 Moda</button>
                <button class="cat-btn" onclick="loadProducts('esporte', this)">⚽ Esporte</button>
                <button class="cat-btn" onclick="loadProducts('informatica', this)">💻 Informática</button>
                <button class="cat-btn" onclick="loadProducts('eletronicos', this)">📱 Eletrônicos</button>
                <button class="cat-btn" onclick="loadProducts('beleza', this)">💄 Beleza</button>
                <button class="cat-btn" onclick="loadProducts('casa', this)">🏠 Casa</button>
            </div>
            
            <div class="info-bar">
                <span id="count">Carregando produtos...</span>
                <span>🔄 Atualizado: <span id="time">Agora</span></span>
            </div>
            
            <div class="grid" id="produtos">
                <div class="loading"><i class="fas fa-spinner"></i><p>Carregando produtos...</p></div>
            </div>
        </div>
        
        <div class="footer">
            <p>🛍️ Shopee Afiliado - Todos os produtos possuem link de afiliado</p>
        </div>

        <script>
            let todosProdutos = [];
            let categoriaAtual = 'todos';
            
            function loadProducts(cat, btn) {
                categoriaAtual = cat;
                document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
                if (btn) btn.classList.add('active');
                
                const grid = document.getElementById('produtos');
                grid.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Carregando produtos...</p></div>';
                
                fetch('/api/products')
                    .then(r => r.json())
                    .then(data => {
                        todosProdutos = data;
                        document.getElementById('count').textContent = `${data.length} produtos encontrados`;
                        document.getElementById('time').textContent = new Date().toLocaleTimeString('pt-BR');
                        renderizar(data);
                    })
                    .catch(() => {
                        grid.innerHTML = '<div class="no-results"><i class="fas fa-exclamation-circle"></i><h3>Erro ao carregar produtos</h3><p>Tente novamente mais tarde</p></div>';
                    });
            }
            
            function renderizar(produtos) {
                const grid = document.getElementById('produtos');
                if (!produtos || produtos.length === 0) {
                    grid.innerHTML = '<div class="no-results"><i class="fas fa-box-open"></i><h3>Nenhum produto encontrado</h3><p>Tente buscar por outro termo</p></div>';
                    return;
                }
                
                grid.innerHTML = produtos.map(p => {
                    const img = p.img || 'https://via.placeholder.com/300x300/ee4d2d/ffffff?text=Shopee';
                    const nome = p.nome || 'Produto sem nome';
                    const link = p.link_afiliado || '#';
                    const comissao = p.comissao || 0;
                    return `
                        <div class="card">
                            <img src="${img}" alt="${nome}" onerror="this.src='https://via.placeholder.com/300x300/ee4d2d/ffffff?text=Produto'">
                            <div class="info">
                                <div class="nome">${nome}</div>
                                <div class="preco">💰 R$ 0,00</div>
                                ${comissao > 0 ? `<div style="font-size:0.8rem;color:#666;margin-bottom:8px;">💸 Comissão: ${comissao.toFixed(1)}%</div>` : ''}
                                <button class="btn-buy" onclick="comprar('${link}')">
                                    <i class="fas fa-shopping-cart"></i> Comprar
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function buscar(event) {
                if (event && event.key !== 'Enter') return;
                const q = document.getElementById('searchInput').value.trim();
                if (!q) { loadProducts(categoriaAtual); return; }
                
                const filtrados = todosProdutos.filter(p => 
                    p.nome && p.nome.toLowerCase().includes(q.toLowerCase())
                );
                document.getElementById('count').textContent = `${filtrados.length} resultados para "${q}"`;
                renderizar(filtrados);
            }
            
            function comprar(link) {
                if (link && link !== '#') {
                    window.open(link, '_blank');
                } else {
                    alert('Link indisponível no momento');
                }
            }
            
            window.onload = function() {
                loadProducts('todos', document.querySelector('.cat-btn'));
            };
        </script>
    </body>
    </html>
    '''

@app.route('/api/products')
def api_products():
    produtos = fetch_products()
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        formatted.append({
            'nome': p.get('productName', ''),
            'img': p.get('imageUrl', ''),
            'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
            'comissao': float(p.get('commissionRate', 0)) * 100
        })
    return jsonify(formatted)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    produtos = fetch_products()
    formatted = []
    for p in produtos:
        link = p.get('productLink', '')
        nome = p.get('productName', '').lower()
        if query.lower() in nome:
            formatted.append({
                'nome': p.get('productName', ''),
                'img': p.get('imageUrl', ''),
                'link_afiliado': f"{link}?mmp_pid=an_{APP_ID}" if link else '#',
                'comissao': float(p.get('commissionRate', 0)) * 100
            })
    return jsonify(formatted[:30])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)