# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from dotenv import load_dotenv
import re
import dns.resolver
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/img'

load_dotenv()

# ============================================
# FUNÇÃO PARA VALIDAR EMAIL (REGEX + DOMÍNIO)
# ============================================
def validar_email(email):
    """
    Valida o formato, domínio e tenta verificar se o email existe
    """
    # 1. Verifica formato
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        return False, "Formato de e-mail inválido! (ex: nome@email.com)"
    
    # 2. Verifica se o domínio existe
    dominio = email.split('@')[1]
    try:
        dns.resolver.resolve(dominio, 'MX')
    except:
        return False, f"O domínio '{dominio}' não existe!"
    
    # 3. Verifica se o email tem formato válido (ex: não é "teste@")
    if email.split('@')[0].strip() == '':
        return False, "Digite um nome de usuário válido antes do @"
    
    # 4. Lista de domínios comuns (se for um domínio comum, provavelmente é válido)
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
# CONTEXT PROCESSOR - VARIÁVEIS GLOBAIS
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
        
        # ===== VALIDAÇÕES =====
        if not nome or not email or not senha:
            mensagem = 'Preencha todos os campos!'
            return render_template('cadastro.html', mensagem=mensagem)
        
        # VERIFICA SE O USUÁRIO ACEITOU OS TERMOS
        if not aceito_termos:
            mensagem = 'Você precisa aceitar os Termos e Condições para criar uma conta!'
            return render_template('cadastro.html', mensagem=mensagem)
        
        if len(senha) < 6:
            mensagem = 'A senha deve ter pelo menos 6 caracteres!'
            return render_template('cadastro.html', mensagem=mensagem)
        
        # VALIDA SE O EMAIL É VÁLIDO
        email_valido, msg_email = validar_email(email)
        if not email_valido:
            mensagem = msg_email
            return render_template('cadastro.html', mensagem=mensagem)
        
        conexao = conectar()
        cursor = conexao.cursor()
        
        # Verifica se o email já está cadastrado
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            mensagem = 'Este e-mail já está cadastrado!'
            cursor.close()
            conexao.close()
            return render_template('cadastro.html', mensagem=mensagem)
        
        # Cria o usuário
        senha_hash = generate_password_hash(senha)
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", 
                      (nome, email, senha_hash))
        conexao.commit()
        
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conexao.close()
        
        if usuario:
            session['usuario'] = usuario[1]
            session['admin'] = usuario[4]
            return redirect('/')
        else:
            mensagem = 'Erro ao criar conta. Tente novamente.'

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
            session['admin'] = usuario[4]
            return redirect('/')
        else:
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
    oauth = OAuth2Session(GOOGLE_CLIENT_ID, scope=SCOPE, 
                         redirect_uri=f"{request.host_url}login/google/authorized")
    authorization_url, state = oauth.authorization_url(
        discovery['authorization_endpoint'], access_type="offline", prompt="select_account"
    )
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
        oauth = OAuth2Session(GOOGLE_CLIENT_ID, scope=SCOPE, 
                             redirect_uri=f"{request.host_url}login/google/authorized",
                             state=state)
        
        oauth.fetch_token(discovery['token_endpoint'], client_secret=GOOGLE_CLIENT_SECRET,
                         authorization_response=request.url)
        
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
            cursor.execute("INSERT INTO usuarios (nome, email, senha, admin) VALUES (%s, %s, %s, %s)",
                          (nome, email, '', 0))
            conexao.commit()
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
        
        cursor.close()
        conexao.close()
        
        if usuario:
            session['usuario'] = usuario[1]
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
    cursor.execute("INSERT INTO avaliacoes (produto_id, usuario, nota, comentario) VALUES (%s, %s, %s, %s)",
                   (produto_id, session['usuario'], request.form.get('nota'), request.form.get('comentario')))
    conexao.commit()
    cursor.close()
    conexao.close()
    
    return redirect(f'/produto/{produto_id}')

# ============================================
# CARRINHO
# ============================================

@app.route('/adicionar_carrinho/<int:id>')
def adicionar_carrinho(id):
    session.setdefault('carrinho', []).append(id)
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
                        'descricao': produto[2],
                        'preco': float(produto[3]),
                        'imagem': produto[4],
                        'is_personalizado': False
                    })
                    total += float(produto[3])

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

    if ids:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in ids:
            if id < 0:
                personalizacao = next((p for p in personalizacoes if p.get('id') == id), None)
                if personalizacao:
                    total += personalizacao.get('preco', 89.90)
            else:
                cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
                produto = cursor.fetchone()
                if produto:
                    total += float(produto[3])

        cursor.execute("INSERT INTO pedidos (usuario, total) VALUES (%s, %s)", (session['usuario'], total))
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
# sustentabiliade
# ============================================
@app.route('/sustentabilidade')
def sustentabilidade():
    return render_template('sustentabilidade.html')

# ============================================
# PERFIL
# ============================================

@app.route('/perfil')
def perfil():
    if not session.get('usuario'):
        return redirect('/login')

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE nome = %s", (session['usuario'],))
    usuario = cursor.fetchone()

    cursor.execute("SELECT COUNT(*), IFNULL(SUM(total),0) FROM pedidos WHERE usuario = %s", (session['usuario'],))
    dados = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('perfil.html', usuario_db=usuario, 
                          total_pedidos=dados[0], total_gasto=dados[1])

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
            SELECT DATE(data) as dia, COUNT(*) as total_pedidos, SUM(total) as valor_total
            FROM pedidos 
            WHERE data >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data) ORDER BY dia ASC
        """)
        vendas_semana = cursor.fetchall()
    except:
        vendas_semana = []

    try:
        cursor.execute("""
            SELECT categoria, COUNT(*) as total
            FROM produtos
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria ORDER BY total DESC
        """)
        distribuicao = cursor.fetchall()
    except:
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
# INICIALIZAÇÃO
# ============================================
if __name__ == '__main__':
    app.run(debug=True)