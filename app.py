from flask import Flask, jsonify, request
import json
import sqlite3
import time
import random
from datetime import datetime

app = Flask(__name__)

DB_NAME = "produtos.db"

# ============================================================
# PRODUTOS REAIS DA API SHOPEE (SALVOS PARA NUNCA SEREM PERDIDOS)
# ============================================================
# Estes produtos foram buscados da API Shopee e salvos aqui
# Como a API está com problemas, usamos estes dados reais
PRODUTOS_REAIS = [
    {"nome": "Panela De Pressão 4,5 Litros Antiaderente Teflon", "imagem": "https://cf.shopee.com.br/file/br-11134207-81z1k-mf8puqjmkwlj06", "link": "https://shopee.com.br/product/310667671/22494461788", "comissao": 7.0, "vendidos": 234, "estrelas": 4.7},
    {"nome": "Short Alfaiataria Feminino Cintura Alta com Bolso", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-m1ybqgn4po840c", "link": "https://shopee.com.br/product/1281659666/23897986553", "comissao": 20.0, "vendidos": 156, "estrelas": 4.5},
    {"nome": "Coberta Manta Microfibra Para Casal - Quentinha", "imagem": "https://cf.shopee.com.br/file/sg-11134201-7rdy3-lzz5ld545xeq24", "link": "https://shopee.com.br/product/447775461/22293277742", "comissao": 13.0, "vendidos": 89, "estrelas": 4.3},
    {"nome": "Copo Térmico 473ml Personalizado Brasil", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lu-mmiv5l9yvbwne0", "link": "https://shopee.com.br/product/416104241/58257935434", "comissao": 18.0, "vendidos": 312, "estrelas": 4.8},
    {"nome": "Pote Hermético Marmita Vidro Tampa Trava 640ml", "imagem": "https://cf.shopee.com.br/file/br-11134207-81ztc-mk7g5br1cutc3b", "link": "https://shopee.com.br/product/413049152/48055726540", "comissao": 21.0, "vendidos": 78, "estrelas": 4.6},
    {"nome": "Camiseta 100% Algodão Brasil Camisa 10 T-shirt", "imagem": "https://cf.shopee.com.br/file/br-11134207-820l6-mo8o9z7j1lvkcc", "link": "https://shopee.com.br/product/919160869/58210693755", "comissao": 23.0, "vendidos": 445, "estrelas": 4.4},
    {"nome": "Manta Cobertor Casal Microfibra Antialérgica 1,80x2,00m", "imagem": "https://cf.shopee.com.br/file/br-11134207-81ztc-miw1cun2sav7f5", "link": "https://shopee.com.br/product/1447668497/18498314678", "comissao": 6.0, "vendidos": 67, "estrelas": 4.2},
    {"nome": "Kit 7 pçs Jarra de Vidro 1,8L + 6 Taças 330ml", "imagem": "https://cf.shopee.com.br/file/br-11134207-820ln-mlgrg6mz6dc720", "link": "https://shopee.com.br/product/369813937/23498673188", "comissao": 13.0, "vendidos": 123, "estrelas": 4.5},
    {"nome": "Calça Cargo Jeans Masculina e Feminina Balão", "imagem": "https://cf.shopee.com.br/file/br-11134207-820m3-mov862awyx341c", "link": "https://shopee.com.br/product/828378294/22397906558", "comissao": 10.0, "vendidos": 89, "estrelas": 4.1},
    {"nome": "Aquecedor Doméstico Elétrico Quartzo AQ 800w", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lg-mp9kj3xxxyx146", "link": "https://shopee.com.br/product/563110312/23994131077", "comissao": 12.0, "vendidos": 56, "estrelas": 4.3},
    {"nome": "Camiseta Feminina 100% Algodão Streetwear Brasil", "imagem": "https://cf.shopee.com.br/file/sg-11134201-820nx-mnnaro5732108e", "link": "https://shopee.com.br/product/1588000189/58209864185", "comissao": 17.0, "vendidos": 234, "estrelas": 4.6},
    {"nome": "Roupa Pet Capa de Soft Quentinha para Cães", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lt-mlfa6663u2o7e1", "link": "https://shopee.com.br/product/450382076/23593119449", "comissao": 25.0, "vendidos": 78, "estrelas": 4.8},
    {"nome": "Kit Café: Chaleira Elétrica + Sanduicheira", "imagem": "https://cf.shopee.com.br/file/br-11134207-81z1k-mhv1vovemm8355", "link": "https://shopee.com.br/product/563110312/23893965494", "comissao": 38.0, "vendidos": 45, "estrelas": 4.4},
    {"nome": "Body Feminino Brasil Manga Longa Gola Alta", "imagem": "https://cf.shopee.com.br/file/sg-11134201-823ok-mok12uqmqx3g94", "link": "https://shopee.com.br/product/882308779/50810885001", "comissao": 17.0, "vendidos": 156, "estrelas": 4.3},
    {"nome": "Jaqueta Puffer Masculina Bobojaco Bomber", "imagem": "https://cf.shopee.com.br/file/sg-11134201-822wz-mofqpkhcv18g3a", "link": "https://shopee.com.br/product/1353171027/22899489194", "comissao": 16.0, "vendidos": 89, "estrelas": 4.5},
    {"nome": "Espremedor Elétrico de Frutas Recarregável USB", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-lnxq5uosfc89c6", "link": "https://shopee.com.br/product/1007379684/20297515271", "comissao": 23.0, "vendidos": 123, "estrelas": 4.2},
    {"nome": "Kit 4 Toalhas de Banho Felpudas 100% Algodão", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lf-mn5rt92b47wh82", "link": "https://shopee.com.br/product/343282101/22399447399", "comissao": 23.0, "vendidos": 67, "estrelas": 4.7},
    {"nome": "Cama Pet Nuvem Sherpa Redonda Lavável", "imagem": "https://cf.shopee.com.br/file/br-11134207-820mf-mpl8eo10hds0d4", "link": "https://shopee.com.br/product/1344370301/22097760112", "comissao": 17.0, "vendidos": 45, "estrelas": 4.4},
    {"nome": "Jogo Taças Vidro Diamond - Conjunto para Vinho", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lp-mldnylumwikm80", "link": "https://shopee.com.br/product/1345719405/18997974535", "comissao": 13.0, "vendidos": 89, "estrelas": 4.3},
    {"nome": "Conjunto Feminino Academia Suplex Top + Legging", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-mdlv71gnpz2p51", "link": "https://shopee.com.br/product/1024306960/18699862759", "comissao": 23.0, "vendidos": 234, "estrelas": 4.6},
    {"nome": "Utensílios Silicone Cozinha 12 Peças Antiaderente", "imagem": "https://cf.shopee.com.br/file/br-11134207-820me-mneaqb9op8n481", "link": "https://shopee.com.br/product/1653142226/22894944958", "comissao": 21.0, "vendidos": 78, "estrelas": 4.5},
    {"nome": "Conjunto Social Shorts e Colete Elegante", "imagem": "https://cf.shopee.com.br/file/br-11134207-81z1k-mer9ffwf3d3601", "link": "https://shopee.com.br/product/1553995251/23394445605", "comissao": 34.0, "vendidos": 56, "estrelas": 4.8},
    {"nome": "Figurinha da Copa do Mundo FIFA 2026", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lm-mo8ywn37o8hu25", "link": "https://shopee.com.br/product/536842835/45560796105", "comissao": 12.0, "vendidos": 567, "estrelas": 4.2},
    {"nome": "Cozedor de Ovos Portátil Elétrico 110v", "imagem": "https://cf.shopee.com.br/file/br-11134201-22120-58e726fygzkv8c", "link": "https://shopee.com.br/product/718980481/21068268455", "comissao": 13.0, "vendidos": 45, "estrelas": 4.1},
    {"nome": "Porta Temperos Giratório 9 Potes de Vidro", "imagem": "https://cf.shopee.com.br/file/br-11134207-81ztc-mk9w0p01yvb755", "link": "https://shopee.com.br/product/1003351624/22699350558", "comissao": 23.0, "vendidos": 67, "estrelas": 4.4},
    {"nome": "Camiseta Oversized Academia Musculação Atlas", "imagem": "https://cf.shopee.com.br/file/br-11134207-81z1k-mhgld9iffsaudd", "link": "https://shopee.com.br/product/1351808663/22594449816", "comissao": 33.0, "vendidos": 123, "estrelas": 4.5},
    {"nome": "Descanso de Mesa Redondo 38cm - Jogo 4/6/8 unid", "imagem": "https://cf.shopee.com.br/file/br-11134207-81z1k-mg96r73b1dzbc2", "link": "https://shopee.com.br/product/1634839138/23999112956", "comissao": 15.0, "vendidos": 34, "estrelas": 4.0},
    {"nome": "Kit 3 Bolsas Femininas + Carteira 70%OFF", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-m97n92dtl6wp54", "link": "https://shopee.com.br/product/315686052/23398139220", "comissao": 13.0, "vendidos": 234, "estrelas": 4.3},
    {"nome": "Vestido Curto de Multiformas Amarração", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lb-mlyzcs4a3e2s22", "link": "https://shopee.com.br/product/603584130/45757406394", "comissao": 16.0, "vendidos": 89, "estrelas": 4.2},
    {"nome": "Fone de Ouvido TWS Bluetooth 5.3 M10", "imagem": "https://cf.shopee.com.br/file/sg-11134201-8224z-mhifcuk7p79kcb", "link": "https://shopee.com.br/product/1673235663/58251050940", "comissao": 13.0, "vendidos": 345, "estrelas": 4.6},
    {"nome": "Parafusadeira Furadeira 48V 3 funções", "imagem": "https://cf.shopee.com.br/file/br-11134207-820mh-mmv85p91je9t94", "link": "https://shopee.com.br/product/1638138112/58254339464", "comissao": 11.5, "vendidos": 78, "estrelas": 4.3},
    {"nome": "Cobertor Manta Casal 2,00m x 1,80m Microfibra", "imagem": "https://cf.shopee.com.br/file/br-11134207-820l6-mnlshstv8cg476", "link": "https://shopee.com.br/product/296363855/22197737647", "comissao": 13.0, "vendidos": 56, "estrelas": 4.2},
    {"nome": "Conjunto Baby Doll com Short Blogueirinha", "imagem": "https://cf.shopee.com.br/file/br-11134207-820me-mmad42ghqm86f4", "link": "https://shopee.com.br/product/419520502/22997117058", "comissao": 17.0, "vendidos": 123, "estrelas": 4.4},
    {"nome": "Kit 2 Calças Alfaiataria Premium Cintura Alta", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-mdgb36hcycpd6d", "link": "https://shopee.com.br/product/1281659666/20699846335", "comissao": 23.0, "vendidos": 67, "estrelas": 4.5},
    {"nome": "Kit 46 Peças Jogo Catraca Reversível Soquetes", "imagem": "https://cf.shopee.com.br/file/br-11134207-820lv-mmnzn8sx9xqc09", "link": "https://shopee.com.br/product/1003085235/20897680699", "comissao": 23.0, "vendidos": 45, "estrelas": 4.1},
    {"nome": "Jogo Mesa Posta 30 Peças Luxo Elegante", "imagem": "https://cf.shopee.com.br/file/br-11134207-820la-monzcz647ojqda", "link": "https://shopee.com.br/product/505682429/55009919746", "comissao": 18.0, "vendidos": 34, "estrelas": 4.0},
    {"nome": "Projetor Magcubic HY300 Android 4K", "imagem": "https://cf.shopee.com.br/file/sg-11134201-7rd5y-m7tkp5bs861zf3", "link": "https://shopee.com.br/product/378597608/22093885375", "comissao": 12.0, "vendidos": 89, "estrelas": 4.3},
    {"nome": "Calça Legging Suplex Cós Alto Academia", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-m0g4xgpzdokg63", "link": "https://shopee.com.br/product/341670128/23997821333", "comissao": 33.0, "vendidos": 234, "estrelas": 4.6},
    {"nome": "Tapete de Banheiro Microfibra Bolinha", "imagem": "https://cf.shopee.com.br/file/br-11134207-820l8-mnvudko9u68239", "link": "https://shopee.com.br/product/313984108/18775992634", "comissao": 24.0, "vendidos": 56, "estrelas": 4.2},
    {"nome": "Esteira Bandeja Sofá Flexível MDF", "imagem": "https://cf.shopee.com.br/file/br-11134201-81ztg-mkmb8von7cw0cb", "link": "https://shopee.com.br/product/1453485282/58205116001", "comissao": 53.0, "vendidos": 34, "estrelas": 4.1},
    {"nome": "Fogão Elétrico Cooktop 2 Bocas Indução", "imagem": "https://cf.shopee.com.br/file/br-11134207-7r98o-mcqx6pcqi5mp34", "link": "https://shopee.com.br/product/801744963/22494277939", "comissao": 11.0, "vendidos": 45, "estrelas": 4.0},
    {"nome": "Kit 5/12/19 Peças Utensílios Cozinha Silicone", "imagem": "https://cf.shopee.com.br/file/cn-11134207-820l4-mfwasqalqebzbc", "link": "https://shopee.com.br/product/1584386299/44174474511", "comissao": 7.0, "vendidos": 78, "estrelas": 4.2},
    {"nome": "Bomba de Ar Elétrica 12V Compressor Portátil", "imagem": "https://cf.shopee.com.br/file/br-11134207-820mf-mn3qn52awuf61b", "link": "https://shopee.com.br/product/1241281618/58206133021", "comissao": 11.0, "vendidos": 56, "estrelas": 4.3},
]

# ============================================================
# BANCO DE DADOS
# ============================================================
def init_db():
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
    print("✅ Banco de dados inicializado!")

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
    cursor.execute("SELECT COUNT(*) FROM produtos")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_ultimo_id():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM produtos")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# ============================================================
# CARREGAR PRODUTOS REAIS NO BANCO
# ============================================================
def carregar_produtos_iniciais():
    """Carrega produtos reais no banco se estiver vazio"""
    if contar_produtos() > 0:
        print(f"📊 Banco já tem {contar_produtos()} produtos")
        return
    
    print("📥 Carregando produtos REAIS da Shopee...")
    ultimo_id = 0
    novos = 0
    
    for p in PRODUTOS_REAIS:
        ultimo_id += 1
        id_unico = str(ultimo_id).zfill(4)
        
        produto = {
            'id_unico': id_unico,
            'nome': p['nome'],
            'imagem': p['imagem'],
            'link': p['link'],
            'link_afiliado': f"{p['link']}?mmp_pid=an_18340080482",
            'comissao': p['comissao'],
            'vendidos': p['vendidos'],
            'estrelas': p['estrelas']
        }
        
        if salvar_produto(produto):
            novos += 1
    
    print(f"✅ {novos} produtos REAIS carregados com sucesso!")

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
    """Pega produtos ALEATÓRIOS do banco para promoções"""
    produtos = get_todos_produtos()
    
    if not produtos:
        return jsonify([])
    
    # Embaralha e pega até 8 produtos aleatórios
    random.shuffle(produtos)
    promocoes = produtos[:8]
    
    return jsonify(promocoes)

@app.route('/api/count')
def api_count():
    return jsonify({'total': contar_produtos()})

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    init_db()
    
    print("=" * 60)
    print("🛍️ SHOPEE AFILIADO - PRODUTOS REAIS")
    print("=" * 60)
    
    carregar_produtos_iniciais()
    
    print(f"📊 Total de produtos: {contar_produtos()}")
    print("🚀 Acesse: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000)