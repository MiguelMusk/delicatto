from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'delicatto2026'

# ============================================
# FUNÇÃO DE CONEXÃO COM O BANCO
# ============================================
import os
from dotenv import load_dotenv

load_dotenv()

def conectar():
    conexao = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_DATABASE')
    )
    return conexao

# ============================================
# CONTEXT PROCESSOR - INJETA VARIÁVEIS GLOBAIS
# ============================================
@app.context_processor
def inject_usuario():
    carrinho = session.get('carrinho', [])
    return dict(
        usuario=session.get('usuario'),
        total_carrinho=len(carrinho)
    )

# ============================================
# HOME
# ============================================
@app.route('/')
def home():
    conexao = conectar()
    cursor = conexao.cursor()
    
    # Pega os 3 primeiros produtos como destaque
    cursor.execute("SELECT * FROM produtos LIMIT 3")
    produtos_destaque = cursor.fetchall()
    
    cursor.close()
    conexao.close()
    
    return render_template('index.html', produtos_destaque=produtos_destaque)

# ============================================
# CADASTRO
# ============================================
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    mensagem = ''

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        senha_hash = generate_password_hash(senha)

        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
        INSERT INTO usuarios (nome, email, senha)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (nome, email, senha_hash))
        conexao.commit()

        cursor.close()
        conexao.close()

        mensagem = 'Conta criada com sucesso!'

    return render_template('cadastro.html', mensagem=mensagem)

# ============================================
# LOGIN
# ============================================
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
            mensagem = 'E-mail ou senha inválidos'

    return render_template('login.html', mensagem=mensagem)

# ============================================
# LOGOUT
# ============================================
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('admin', None)
    session.pop('carrinho', None)
    return redirect('/')

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


# ============================================
# PRODUTO DETALHE
# ============================================
@app.route('/produto/<int:id>')
def produto(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
    produto = cursor.fetchone()

    cursor.execute("""
        SELECT usuario, nota, comentario
        FROM avaliacoes
        WHERE produto_id=%s
        ORDER BY id DESC
    """, (id,))
    avaliacoes = cursor.fetchall()

    cursor.execute("""
        SELECT AVG(nota), COUNT(*)
        FROM avaliacoes
        WHERE produto_id=%s
    """, (id,))
    estatisticas = cursor.fetchone()

    media = estatisticas[0] or 0
    quantidade = estatisticas[1] or 0

    cursor.close()
    conexao.close()

    return render_template(
        'produto.html',
        produto=produto,
        avaliacoes=avaliacoes,
        media=media,
        quantidade=quantidade
    )

# ============================================
# CARRINHO
# ============================================
@app.route('/carrinho')
def carrinho():
    ids = session.get('carrinho', [])
    produtos_carrinho = []
    total = 0

    if ids:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in ids:
            cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
            produto = cursor.fetchone()
            if produto:
                produtos_carrinho.append(produto)
                total += float(produto[3])

        cursor.close()
        conexao.close()

    return render_template('carrinho.html', produtos=produtos_carrinho, total=total)

@app.route('/adicionar_carrinho/<int:id>')
def adicionar_carrinho(id):
    if 'carrinho' not in session:
        session['carrinho'] = []

    carrinho = session['carrinho']
    carrinho.append(id)
    session['carrinho'] = carrinho

    return redirect('/produtos')

@app.route('/remover_carrinho/<int:id>')
def remover_carrinho(id):
    carrinho = session.get('carrinho', [])
    if id in carrinho:
        carrinho.remove(id)
    session['carrinho'] = carrinho
    return redirect('/carrinho')

# ============================================
# FINALIZAR COMPRA
# ============================================
@app.route('/finalizar_compra')
def finalizar_compra():
    if not session.get('usuario'):
        return redirect('/login')

    ids = session.get('carrinho', [])
    total = 0

    if ids:
        conexao = conectar()
        cursor = conexao.cursor()

        for id in ids:
            cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
            produto = cursor.fetchone()
            if produto:
                total += float(produto[3])

        cursor.execute("""
            INSERT INTO pedidos (usuario, total)
            VALUES (%s, %s)
        """, (session['usuario'], total))

        conexao.commit()
        cursor.close()
        conexao.close()

    session['carrinho'] = []
    return redirect('/pedido_sucesso')

@app.route('/pedido_sucesso')
def pedido_sucesso():
    return render_template('pedido_sucesso.html')

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

    cursor.execute("""
        SELECT COUNT(*), IFNULL(SUM(total),0)
        FROM pedidos
        WHERE usuario = %s
    """, (session['usuario'],))
    dados = cursor.fetchone()

    total_pedidos = dados[0]
    total_gasto = dados[1]

    cursor.close()
    conexao.close()

    return render_template(
        'perfil.html',
        usuario_db=usuario,
        total_pedidos=total_pedidos,
        total_gasto=total_gasto
    )

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
        descricao_completa = request.form.get('descricao_completa')
        modo_uso = request.form.get('modo_uso')
        beneficios = request.form.get('beneficios')
        ingredientes = request.form.get('ingredientes')
        categoria = request.form.get('categoria')

        nome_arquivo = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))

        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
        INSERT INTO produtos
        (nome, descricao, preco, imagem, descricao_completa, modo_uso, beneficios, ingredientes, categoria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (nome, descricao, preco, nome_arquivo, descricao_completa, modo_uso, beneficios, ingredientes, categoria))
        conexao.commit()
        cursor.close()
        conexao.close()

        mensagem = 'Produto adicionado com sucesso!'

    # ===== BUSCAR DADOS PARA O ADMIN =====
    conexao = conectar()
    cursor = conexao.cursor()

    # 1. Produtos
    cursor.execute("SELECT * FROM produtos ORDER BY id DESC")
    produtos = cursor.fetchall()

    # 2. Total de usuários
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]

    # 3. Total de pedidos
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    # 4. Total de avaliações
    cursor.execute("SELECT COUNT(*) FROM avaliacoes")
    total_avaliacoes = cursor.fetchone()[0]

    # 5. Lista de usuários
    cursor.execute("SELECT id, nome, email, admin FROM usuarios ORDER BY id DESC")
    usuarios = cursor.fetchall()

    # 6. Vendas dos últimos 7 dias
    try:
        cursor.execute("""
            SELECT 
                DATE(data) as dia, 
                COUNT(*) as total_pedidos, 
                SUM(total) as valor_total
            FROM pedidos 
            WHERE data >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data) 
            ORDER BY dia ASC
        """)
        vendas_semana = cursor.fetchall()
    except:
        vendas_semana = []

    # ===== 7. DISTRIBUIÇÃO DE PRODUTOS POR CATEGORIA =====
    try:
        cursor.execute("""
            SELECT categoria, COUNT(*) as total
            FROM produtos
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY total DESC
        """)
        distribuicao = cursor.fetchall()
        
        if not distribuicao:
            distribuicao = []
    except Exception as e:
        print(f"Erro na consulta de distribuição: {e}")
        distribuicao = []

    cursor.close()
    conexao.close()

    return render_template(
        'admin.html',
        mensagem=mensagem,
        produtos=produtos,
        total_usuarios=total_usuarios,
        total_pedidos=total_pedidos,
        total_avaliacoes=total_avaliacoes,
        usuarios=usuarios,
        vendas_semana=vendas_semana,
        distribuicao=distribuicao
    )
# ============================================
# DELETAR PRODUTO
# ============================================
@app.route('/deletar_produto/<int:id>')
def deletar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
    conexao.commit()
    cursor.close()
    conexao.close()
    return redirect('/admin')

# ============================================
# EDITAR PRODUTO
# ============================================
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        descricao_completa = request.form.get('descricao_completa')
        modo_uso = request.form.get('modo_uso')
        beneficios = request.form.get('beneficios')
        ingredientes = request.form.get('ingredientes')
        categoria = request.form.get('categoria')

        # Verifica se uma nova imagem foi enviada
        imagem = request.files.get('imagem')
        
        if imagem and imagem.filename != '':
            nome_arquivo = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
        else:
            # Mantém a imagem atual
            cursor.execute("SELECT imagem FROM produtos WHERE id = %s", (id,))
            resultado = cursor.fetchone()
            nome_arquivo = resultado[0] if resultado else None

        cursor.execute("""
            UPDATE produtos
            SET nome=%s, descricao=%s, preco=%s, imagem=%s,
                descricao_completa=%s, modo_uso=%s, beneficios=%s, ingredientes=%s
            WHERE id=%s
        """, (nome, descricao, preco, nome_arquivo, descricao_completa, modo_uso, beneficios, ingredientes, id))

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
# AVALIAÇÕES
# ============================================
@app.route('/avaliar/<int:produto_id>', methods=['POST'])
def avaliar(produto_id):
    if not session.get('usuario'):
        return redirect('/login')

    nota = request.form.get('nota')
    comentario = request.form.get('comentario')

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO avaliacoes (produto_id, usuario, nota, comentario)
        VALUES (%s, %s, %s, %s)
    """, (produto_id, session['usuario'], nota, comentario))

    conexao.commit()
    cursor.close()
    conexao.close()

    return redirect(f'/produto/{produto_id}')

# ============================================
# SKINMATCH
# ============================================
@app.route('/skinmatch')
def skinmatch():
    return render_template('skinmatch.html')

# ============================================
# SOBRE
# ============================================
@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# ============================================
# CONTATO
# ============================================
@app.route('/contato')
def contato():
    return render_template('contato.html')

# ============================================
# PÁGINAS LEGAIS
# ============================================
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