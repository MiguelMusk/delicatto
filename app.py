# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from dotenv import load_dotenv
import re
import dns.resolver
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/img'

# ============================================
# SKINMATCH COM O GROQ
# ============================================
from groq import Groq

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if not GROQ_API_KEY:
    print("ATENÇÃO: GROQ_API_KEY não configurado! SkinMatch IA não funcionará.")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
GROQ_MODEL = "openai/gpt-oss-120b"

# ============================================
# FUNÇÃO PARA VALIDAR EMAIL
# ============================================
def validar_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        return False, "Formato de e-mail inválido! (ex: nome@email.com)"

    dominio = email.split('@')[1]
    try:
        dns.resolver.resolve(dominio, 'MX')
    except:
        return False, f"O domínio '{dominio}' não existe!"

    if email.split('@')[0].strip() == '':
        return False, "Digite um nome de usuário válido antes do @"

    dominios_confiaveis = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com',
                           'uol.com.br', 'bol.com.br', 'terra.com.br', 'icloud.com',
                           'protonmail.com', 'mail.com', 'live.com', 'msn.com']

    if dominio in dominios_confiaveis:
        return True, "E-mail válido!"

    return True, "E-mail válido (domínio verificado, mas não foi possível confirmar a conta)"

# ============================================
# BANCO DE DADOS
# ============================================
def conectar():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_DATABASE')
    )

# ============================================
# SKINMATCH IA - GERADOR DE DIAGNÓSTICO 
# ============================================
def gerar_diagnostico_ia(perfil_pele):
    if not groq_client:
        return None, "Serviço de IA não configurado. Configure GROQ_API_KEY no .env"

    prompt = f"""Você é um dermatologista especializado em skincare da marca Delicatto Cosméticos.

Com base no perfil de pele abaixo, gere um diagnóstico dermatológico (mas realista e profissional), seguido de uma rotina de cuidados personalizada.

PERFIL DA PELE:
- Tipo de pele: {perfil_pele.get('tipo_pele', 'não informado')}
- Pele sensível: {perfil_pele.get('sensivel', 'não informado')}
- Principal objetivo: {perfil_pele.get('objetivo', 'não informado')}
- Tendência a acne: {perfil_pele.get('acne', 'não informado')}
- Sensação após lavar o rosto: {perfil_pele.get('sente_apos_lavar', 'não informado')}
- Frequência de maquiagem: {perfil_pele.get('maquiagem', 'não informado')}
- Exposição solar: {perfil_pele.get('exposicao_sol', 'não informado')}

INSTRUÇÕES:
1. Escreva em português brasileiro
2. Seja profissional, acessível e acolhedor
3. Estruture a resposta EXATAMENTE neste formato:

**DIAGNÓSTICO**
[Um parágrafo de análise profissional]

**ROTINA RECOMENDADA**
1. [Passo 1]
2. [Passo 2]
3. [Passo 3]
4. [Passo 4]

**RECOMENDAÇÃO FINAL**
[Uma frase com dica prática]

4. Máximo de 250 palavras
5. NÃO prescreva medicamentos ou tratamentos médicos reais
6. Deixe claro que é uma análise para fins de demonstração e que sempre é recomendavél ter recomendações médicas reais.

Responda APENAS com o diagnóstico, sem explicações adicionais:"""

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,     
            temperature=0.7,
        )
        diagnostico = completion.choices[0].message.content
        if not diagnostico or diagnostico.strip() == "":
            return None, "A IA retornou uma resposta vazia."
        return diagnostico, None
    except Exception as e:
        print(f"Erro ao chamar API do Groq: {e}")
        return None, f"Erro ao gerar diagnóstico: {str(e)}"

# ============================================
# CONTEXT PROCESSOR
# ============================================
@app.context_processor
def inject_usuario():
    carrinho = session.get('carrinho', [])
    personalizacoes = session.get('personalizacoes', [])
    total_valor = 0
    produtos_carrinho = []

    if carrinho:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in carrinho:
            if id < 0:
                personalizacao = next((p for p in personalizacoes if p.get('id') == id), None)
                if personalizacao:
                    produtos_carrinho.append({
                     'id': id,
                        'nome': f" {personalizacao.get('produto_nome', 'Produto Personalizado')}",
                        'preco': personalizacao.get('preco', 89.90),
                        'imagem': 'personalizado.png',
                        'is_personalizado': True,
                        'detalhes': personalizacao
                    })
                    total_valor += personalizacao.get('preco', 89.90)
            else:
                cursor.execute("SELECT id, nome, preco, imagem FROM produtos WHERE id = %s", (id,))
                produto = cursor.fetchone()
                if produto:
                    produtos_carrinho.append({
                        'id': produto[0],
                        'nome': produto[1],
                        'preco': float(produto[2]),
                        'imagem': produto[3],
                        'is_personalizado': False
                    })
                    total_valor += float(produto[2])

        cursor.close()
        conexao.close()

    return dict(
        usuario=session.get('usuario'),
        total_carrinho=len(carrinho),
        total_carrinho_valor=total_valor,
        produtos_carrinho_resumo=produtos_carrinho
    )

# ============================================
# ROTAS PRINCIPAIS
# ============================================
@app.route('/')
def home():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM produtos LIMIT 3")
    produtos_destaque = cursor.fetchall()
    cursor.close()
    conexao.close()
    return render_template('index.html', produtos_destaque=produtos_destaque)

# ============================================
# AUTENTICAÇÃO
# ============================================
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    mensagem = ''
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        aceito_termos = request.form.get('aceito_termos')

        if not nome or not email or not senha:
            return render_template('cadastro.html', mensagem='Preencha todos os campos!')

        if not aceito_termos:
            return render_template('cadastro.html', mensagem='Você precisa aceitar os Termos e Condições!')

        if len(senha) < 6:
            return render_template('cadastro.html', mensagem='A senha deve ter pelo menos 6 caracteres!')

        email_valido, msg_email = validar_email(email)
        if not email_valido:
            return render_template('cadastro.html', mensagem=msg_email)

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conexao.close()
            return render_template('cadastro.html', mensagem='Este e-mail já está cadastrado!')

        senha_hash = generate_password_hash(senha)
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha_hash))
        conexao.commit()

        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()

        if usuario:
            session['usuario'] = usuario[1]
            session['usuario_id'] = usuario[0]
            session['admin'] = usuario[4]
            return redirect('/')
        mensagem = 'Erro ao criar conta.'

    return render_template('cadastro.html', mensagem=mensagem)

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()

        if usuario and check_password_hash(usuario[3], senha):
            session['usuario'] = usuario[1]
            session['usuario_id'] = usuario[0]
            session['admin'] = usuario[4]
            return redirect('/')
        mensagem = 'E-mail ou senha inválidos!'

    return render_template('login.html', mensagem=mensagem)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ============================================
# LOGIN COM GOOGLE
# ============================================
from requests_oauthlib import OAuth2Session
import requests

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("ATENÇÃO: Credenciais do Google não encontradas no .env!")

SCOPE = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

@app.route('/login/google')
def login_google():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return "Erro: Credenciais do Google não configuradas", 500

    discovery = requests.get(GOOGLE_DISCOVERY_URL).json()
    oauth = OAuth2Session(GOOGLE_CLIENT_ID, scope=SCOPE, redirect_uri=f"{request.host_url}login/google/authorized")
    authorization_url, state = oauth.authorization_url(discovery['authorization_endpoint'], access_type="offline", prompt="select_account")
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/login/google/authorized')
def google_authorized():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return "Erro: Credenciais do Google não configuradas", 500

    code = request.args.get('code')
    state = request.args.get('state')
    if not code:
        return redirect('/login')

    try:
        discovery = requests.get(GOOGLE_DISCOVERY_URL).json()
        oauth = OAuth2Session(GOOGLE_CLIENT_ID, scope=SCOPE, redirect_uri=f"{request.host_url}login/google/authorized", state=state)
        oauth.fetch_token(discovery['token_endpoint'], client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)
        user_info = oauth.get(discovery['userinfo_endpoint']).json()
        email = user_info.get('email')
        nome = user_info.get('name')

        if not email:
            return redirect('/login')

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            cursor.execute("INSERT INTO usuarios (nome, email, senha, admin) VALUES (%s, %s, %s, %s)", (nome, email, '', 0))
            conexao.commit()
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()

        cursor.close()
        conexao.close()

        if usuario:
            session['usuario'] = usuario[1]
            session['usuario_id'] = usuario[0]
            session['admin'] = usuario[4]
            session.pop('oauth_state', None)
            return redirect('/')
    except Exception as e:
        print(f"Erro no login com Google: {e}")

    return redirect('/login')

# ============================================
# PRODUTOS
# ============================================
@app.route('/produtos')
def produtos():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/produto/<int:id>')
def produto(id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
    produto = cursor.fetchone()

    if not produto:
        cursor.close()
        conexao.close()
        return redirect('/produtos')

    cursor.execute("SELECT usuario, nota, comentario FROM avaliacoes WHERE produto_id=%s ORDER BY id DESC", (id,))
    avaliacoes = cursor.fetchall()

    cursor.execute("SELECT AVG(nota), COUNT(*) FROM avaliacoes WHERE produto_id=%s", (id,))
    estatisticas = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('produto.html', produto=produto, avaliacoes=avaliacoes,
                           media=estatisticas[0] or 0, quantidade=estatisticas[1] or 0)

@app.route('/avaliar/<int:produto_id>', methods=['POST'])
def avaliar(produto_id):
    if not session.get('usuario'):
        return redirect('/login')

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO avaliacoes (produto_id, usuario_id, usuario, nota, comentario) VALUES (%s, %s, %s, %s, %s)",
                   (produto_id, session.get('usuario_id'), session['usuario'], request.form.get('nota'), request.form.get('comentario')))
    conexao.commit()
    cursor.close()
    conexao.close()

    return redirect(f'/produto/{produto_id}')

# ============================================
# CARRINHO
# ============================================
@app.route('/adicionar_carrinho/<int:id>')
def adicionar_carrinho(id):
    # Verifica se o produto existe antes de adicionar
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM produtos WHERE id = %s", (id,))
    existe = cursor.fetchone()
    cursor.close()
    conexao.close()

    if existe:
        session.setdefault('carrinho', []).append(id)
        session.modified = True
        print(f" Produto {id} adicionado ao carrinho. Carrinho atual: {session['carrinho']}")
    else:
        print(f"⚠️ Tentativa de adicionar produto inexistente (ID: {id})")
        
    return redirect('/produtos')

@app.route('/remover_carrinho/<int:id>')
def remover_carrinho(id):
    carrinho = session.get('carrinho', [])
    if id in carrinho:
        carrinho.remove(id)
    session['carrinho'] = carrinho
    return redirect('/carrinho')

@app.route('/carrinho', methods=['GET', 'POST'])
def carrinho():
    ids = session.get('carrinho', [])
    personalizacoes = session.get('personalizacoes', [])
    produtos_carrinho = []
    total = 0

    # ===== ESPIÃO DE DEBUG =====
    print("=" * 40)
    print("IDS NO CARRINHO:", ids)
    # ===========================

    if ids:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in ids:
            if id < 0:
                personalizacao = next((p for p in personalizacoes if p.get('id') == id), None)
                if personalizacao:
                    produtos_carrinho.append({
                        'id': id,
                        'nome': f"{personalizacao.get('produto_nome', 'Produto Personalizado')}",
                        'descricao': f"Personalizado para {personalizacao.get('nome', '')}",
                        'preco': personalizacao.get('preco', 89.90),
                        'imagem': 'personalizado.png',
                        'is_personalizado': True,
                        'detalhes': personalizacao
                    })
                    total += personalizacao.get('preco', 89.90)
            else:
                cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
                produto = cursor.fetchone()
                if produto:
                    produtos_carrinho.append({
                        'id': produto[0],
                        'nome': produto[1],
                        'descricao': produto[2] if produto[2] else '',
                        'preco': float(produto[3]),
                        'imagem': produto[4],
                        'is_personalizado': False
                    })
                    total += float(produto[3])
                else:
                    print(f"⚠️ Produto ID {id} não encontrado no banco.")

        cursor.close()
        conexao.close()

    cupom = request.args.get('cupom') or request.form.get('cupom')
    remover = request.args.get('remover')

    desconto = 0
    total_com_desconto = total
    cupom_valido = False
    mensagem_cupom = ''
    cupom_aplicado = None

    if remover == 'true':
        mensagem_cupom = 'Cupom removido com sucesso!'
    elif cupom:
        cupom = cupom.upper()
        cupom_aplicado = cupom

        if cupom == 'DELICATTO10':
            desconto = total * 0.10
            total_com_desconto = total - desconto
            cupom_valido = True
            mensagem_cupom = f'Cupom {cupom} aplicado! 10% de desconto'
        elif cupom == 'DELICATTO20':
            desconto = total * 0.20
            total_com_desconto = total - desconto
            cupom_valido = True
            mensagem_cupom = f'Cupom {cupom} aplicado! 20% de desconto'
        elif cupom == 'MIGUELLINDO':
            desconto = total
            total_com_desconto = 0
            cupom_valido = True
            mensagem_cupom = f'😈 Cupom {cupom} aplicado! se vc achou isso parebéns! esse é nosso segredinho...!'
        else:
            mensagem_cupom = 'Cupom inválido'
            cupom_aplicado = None

    return render_template('carrinho.html', produtos=produtos_carrinho, total=total,
                           total_com_desconto=total_com_desconto, desconto=desconto,
                           cupom_valido=cupom_valido, mensagem_cupom=mensagem_cupom,
                           cupom_aplicado=cupom_aplicado)

@app.route('/finalizar_compra')
def finalizar_compra():
    if not session.get('usuario'):
        return redirect('/login')

    ids = session.get('carrinho', [])
    personalizacoes = session.get('personalizacoes', [])
    total = 0
    itens_pedido = []

    if ids:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in ids:
            if id < 0:
                personalizacao = next((p for p in personalizacoes if p.get('id') == id), None)
                if personalizacao:
                    preco = personalizacao.get('preco', 89.90)
                    total += preco
                    itens_pedido.append({
                        'produto_id': None,
                        'nome': personalizacao.get('produto_nome', 'Produto Personalizado'),
                        'preco': preco,
                        'is_personalizado': True,
                        'detalhes': json.dumps(personalizacao)
                    })
            else:
                cursor.execute("SELECT id, nome, preco FROM produtos WHERE id=%s", (id,))
                produto = cursor.fetchone()
                if produto:
                    preco = float(produto[2])
                    total += preco
                    itens_pedido.append({
                        'produto_id': produto[0],
                        'nome': produto[1],
                        'preco': preco,
                        'is_personalizado': False,
                        'detalhes': None
                    })

        # Insere o pedido
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, usuario, total, status) VALUES (%s, %s, %s, %s)",
            (session.get('usuario_id'), session['usuario'], total, 'preparando')
        )
        pedido_id = cursor.lastrowid
        print(f" Pedido #{pedido_id} criado. Total: R$ {total}")

        for item in itens_pedido:
            print(f"   -> Salvando item: {item['nome']} | Preço: {item['preco']}")
            cursor.execute("""
                INSERT INTO pedido_itens 
                (pedido_id, produto_id, nome_produto, preco_unitario, quantidade, is_personalizado, detalhes_personalizacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (pedido_id, item['produto_id'], item['nome'], item['preco'], 1, item['is_personalizado'], item['detalhes']))

        conexao.commit()
        cursor.close()
        conexao.close()

    session['carrinho'] = []
    session.pop('personalizacoes', None)
    return redirect('/pedido_sucesso')

@app.route('/pedido_sucesso')
def pedido_sucesso():
    return render_template('pedido_sucesso.html')

# ============================================
# PERSONALIZAÇÃO
# ============================================
@app.route('/personalizacao')
def personalizacao():
    return render_template('personalizacao.html')

@app.route('/adicionar_personalizado', methods=['POST'])
def adicionar_personalizado():
    session.setdefault('carrinho', [])
    session.setdefault('personalizacoes', [])

    produto_base = request.form.get('produto_base')
    nome = request.form.get('nome_rotulo')

    nomes_produtos = {
        'hidratante_corporal': 'Hidratante Corporal',
        'serum_facial': 'Sérum Facial',
        'creme_revitalizante': 'Creme Revitalizante',
        'body_splash': 'Body Splash'
    }

    precos_produtos = {
        'hidratante_corporal': 89.90,
        'serum_facial': 129.90,
        'creme_revitalizante': 99.90,
        'body_splash': 79.90
    }

    import time
    produto_id = int(time.time()) * -1

    session['carrinho'].append(produto_id)

    session['personalizacoes'].append({
        'id': produto_id,
        'nome': nome or 'Seu Nome',
        'pele': request.form.get('pele'),
        'fragrancia': request.form.get('fragrancia'),
        'objetivo': request.form.get('objetivo'),
        'mensagem': request.form.get('mensagem'),
        'cor': request.form.get('cor_embalagem', 'roxo'),
        'cor_fonte': request.form.get('cor_fonte', 'branco'),
        'produto_nome': nomes_produtos.get(produto_base, 'Produto Personalizado'),
        'preco': precos_produtos.get(produto_base, 89.90)
    })

    session.modified = True
    return redirect('/carrinho')

@app.route('/remover_perso/<id>')
def remover_perso(id):
    carrinho = session.get('carrinho', [])
    try:
        id_int = int(id)
        if id_int in carrinho:
            carrinho.remove(id_int)
            session['carrinho'] = carrinho
    except:
        pass

    session['personalizacoes'] = [p for p in session.get('personalizacoes', []) if str(p.get('id')) != str(id)]
    session.modified = True
    return redirect('/carrinho')

# ============================================
# SUSTENTABILIDADE
# ============================================
@app.route('/sustentabilidade')
def sustentabilidade():
    return render_template('sustentabilidade.html')

# ============================================
# PERFIL (BLINDADO)
# ============================================
@app.route('/perfil')
def perfil():
    if not session.get('usuario_id'):
        return redirect('/login')

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT id, nome, email, telefone, admin, criado_em FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conexao.close()
        return redirect('/logout')

    cursor.execute("SELECT COUNT(*) AS total_pedidos, IFNULL(SUM(total),0) AS total_gasto FROM pedidos WHERE usuario_id = %s", (session['usuario_id'],))
    stats = cursor.fetchone()

    cursor.execute("SELECT id, total, data_pedido, status FROM pedidos WHERE usuario_id = %s ORDER BY data_pedido DESC LIMIT 10", (session['usuario_id'],))
    pedidos = cursor.fetchall()

    for pedido in pedidos:
        cursor_itens = conexao.cursor() 
        cursor_itens.execute("SELECT nome_produto, quantidade, preco_unitario FROM pedido_itens WHERE pedido_id = %s", (pedido['id'],))
        itens = cursor_itens.fetchall()
        pedido['itens'] = [{'nome_produto': i[0], 'quantidade': i[1], 'preco_unitario': i[2]} for i in itens]
        cursor_itens.close()

    cursor.execute("""
        SELECT a.nota, a.comentario, p.nome AS produto_nome, p.id AS produto_id
        FROM avaliacoes a
        JOIN produtos p ON p.id = a.produto_id
        WHERE a.usuario_id = %s
        ORDER BY a.id DESC LIMIT 3
    """, (session['usuario_id'],))
    avaliacoes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('perfil.html', usuario_db=usuario, total_pedidos=stats['total_pedidos'],
                           total_gasto=stats['total_gasto'], pedidos=pedidos, avaliacoes=avaliacoes)

@app.route('/perfil/editar', methods=['POST'])
def perfil_editar():
    if not session.get('usuario_id'):
        return redirect('/login')

    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    telefone = request.form.get('telefone', '').strip()

    if not nome or not email:
        session['msg_perfil'] = 'Nome e e-mail são obrigatórios.'
        session['msg_perfil_tipo'] = 'erro'
        return redirect('/perfil')

    email_valido, msg_email = validar_email(email)
    if not email_valido:
        session['msg_perfil'] = msg_email
        session['msg_perfil_tipo'] = 'erro'
        return redirect('/perfil')

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, session['usuario_id']))
    if cursor.fetchone():
        session['msg_perfil'] = 'Este e-mail já está em uso.'
        session['msg_perfil_tipo'] = 'erro'
        cursor.close()
        conexao.close()
        return redirect('/perfil')

    nome_antigo = session['usuario']

    cursor.execute("UPDATE usuarios SET nome = %s, email = %s, telefone = %s WHERE id = %s", (nome, email, telefone, session['usuario_id']))
    
    if nome_antigo != nome:
        cursor.execute("UPDATE pedidos SET usuario = %s WHERE usuario_id = %s", (nome, session['usuario_id']))
        cursor.execute("UPDATE avaliacoes SET usuario = %s WHERE usuario_id = %s", (nome, session['usuario_id']))

    conexao.commit()
    cursor.close()
    conexao.close()

    session['usuario'] = nome
    session['msg_perfil'] = 'Dados atualizados com sucesso!'
    session['msg_perfil_tipo'] = 'sucesso'
    return redirect('/perfil')

@app.route('/perfil/senha', methods=['POST'])
def perfil_senha():
    if not session.get('usuario_id'):
        return redirect('/login')

    senha_atual = request.form.get('senha_atual')
    senha_nova = request.form.get('senha_nova')
    senha_confirma = request.form.get('senha_confirma')

    if not senha_atual or not senha_nova or not senha_confirma:
        session['msg_perfil'] = 'Preencha todos os campos de senha.'
        session['msg_perfil_tipo'] = 'erro'
        return redirect('/perfil')

    if len(senha_nova) < 6:
        session['msg_perfil'] = 'A nova senha deve ter pelo menos 6 caracteres.'
        session['msg_perfil_tipo'] = 'erro'
        return redirect('/perfil')

    if senha_nova != senha_confirma:
        session['msg_perfil'] = 'As senhas novas não coincidem.'
        session['msg_perfil_tipo'] = 'erro'
        return redirect('/perfil')

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT senha FROM usuarios WHERE id = %s", (session['usuario_id'],))
    resultado = cursor.fetchone()

    if not resultado or not check_password_hash(resultado[0], senha_atual):
        session['msg_perfil'] = 'Senha atual incorreta.'
        session['msg_perfil_tipo'] = 'erro'
        cursor.close()
        conexao.close()
        return redirect('/perfil')

    nova_hash = generate_password_hash(senha_nova)
    cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (nova_hash, session['usuario_id']))
    conexao.commit()
    cursor.close()
    conexao.close()

    session['msg_perfil'] = 'Senha alterada com sucesso!'
    session['msg_perfil_tipo'] = 'sucesso'
    return redirect('/perfil')

# ============================================
# ADMIN
# ============================================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect('/')

    mensagem = ''

    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        imagem = request.files['imagem']

        nome_arquivo = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO produtos (nome, descricao, preco, imagem, descricao_completa, modo_uso, beneficios, ingredientes, categoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nome, descricao, preco, nome_arquivo,
              request.form.get('descricao_completa'), request.form.get('modo_uso'),
              request.form.get('beneficios'), request.form.get('ingredientes'), request.form.get('categoria')))
        conexao.commit()
        cursor.close()
        conexao.close()
        mensagem = 'Produto adicionado com sucesso!'

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM produtos ORDER BY id DESC")
    produtos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM avaliacoes")
    total_avaliacoes = cursor.fetchone()[0]

    cursor.execute("SELECT id, nome, email, admin FROM usuarios ORDER BY id DESC")
    usuarios = cursor.fetchall()

    try:
        cursor.execute("""
            SELECT DATE(data_pedido) as dia, COUNT(*) as total_pedidos, SUM(total) as valor_total
            FROM pedidos
            WHERE data_pedido >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data_pedido) ORDER BY dia ASC
        """)
        vendas_semana = cursor.fetchall()
    except Exception as e:
        print(f"Erro no gráfico de vendas: {e}")
        vendas_semana = []

    try:
        cursor.execute("""
            SELECT categoria, COUNT(*) as total
            FROM produtos
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria ORDER BY total DESC
        """)
        distribuicao = cursor.fetchall()
    except Exception as e:
        print(f"Erro no gráfico de distribuição: {e}")
        distribuicao = []

    cursor.close()
    conexao.close()

    return render_template('admin.html', mensagem=mensagem, produtos=produtos,
                           total_usuarios=total_usuarios, total_pedidos=total_pedidos,
                           total_avaliacoes=total_avaliacoes, usuarios=usuarios,
                           vendas_semana=vendas_semana, distribuicao=distribuicao)

@app.route('/deletar_produto/<int:id>')
def deletar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
    conexao.commit()
    cursor.close()
    conexao.close()
    return redirect('/admin')

@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')

        imagem = request.files.get('imagem')
        if imagem and imagem.filename != '':
            nome_arquivo = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
        else:
            cursor.execute("SELECT imagem FROM produtos WHERE id = %s", (id,))
            nome_arquivo = cursor.fetchone()[0]

        cursor.execute("""
            UPDATE produtos
            SET nome=%s, descricao=%s, preco=%s, imagem=%s,
                descricao_completa=%s, modo_uso=%s, beneficios=%s, ingredientes=%s, categoria=%s
            WHERE id=%s
        """, (nome, descricao, preco, nome_arquivo,
              request.form.get('descricao_completa'), request.form.get('modo_uso'),
              request.form.get('beneficios'), request.form.get('ingredientes'),
              request.form.get('categoria'), id))

        conexao.commit()
        cursor.close()
        conexao.close()
        return redirect('/admin')

    cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()

    return render_template('editar_produto.html', produto=produto)

# ============================================
# PÁGINAS ESTÁTICAS
# ============================================
@app.route('/skinmatch')
def skinmatch():
    return render_template('skinmatch.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/politica_privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html')

@app.route('/termos_condicoes')
def termos_condicoes():
    return render_template('termos_condicoes.html')

# ============================================
# API SKINMATCH IA
# ============================================
@app.route('/api/skinmatch/diagnostico', methods=['POST'])
def skinmatch_diagnostico():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados não enviados'}), 400

    usos = session.get('ia_usos', 0)
    if usos >= 10:
        return jsonify({'erro': 'Limite de uso da IA atingido. Recarregue a página para continuar.'}), 429
    session['ia_usos'] = usos + 1

    perfil = {
        'tipo_pele': data.get('tipo_pele'),
        'sensivel': data.get('sensivel'),
        'objetivo': data.get('objetivo'),
        'acne': data.get('acne'),
        'sente_apos_lavar': data.get('sente_apos_lavar'),
        'maquiagem': data.get('maquiagem'),
        'exposicao_sol': data.get('exposicao_sol'),
    }

    diagnostico, erro = gerar_diagnostico_ia(perfil)

    if erro:
        return jsonify({'erro': erro}), 500

    return jsonify({'diagnostico': diagnostico, 'perfil': perfil})

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == '__main__':
    app.run(debug=True)