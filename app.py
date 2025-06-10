# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session # type: ignore
import sqlite3
import shutil
import datetime
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
DB_NAME = os.path.join(os.path.dirname(__file__), 'pdv.db')

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                preco REAL NOT NULL,
                estoque INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                total REAL,
                forma_pagamento TEXT,
                data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                FOREIGN KEY(produto_id) REFERENCES produtos(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        ''')
        conn.commit()

def backup_db():
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DB_NAME, f"backups/pdv_backup_{now}.db")

@app.route('/')
def index():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE nome=? AND senha=?", (nome, senha))
            user = cursor.fetchone()

        if user:
            session['usuario_logado'] = nome
            return redirect(url_for('index'))
        else:
            return "<p>Usuário ou senha incorretos.</p>"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    return redirect(url_for('login'))

@app.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])

        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
                               (nome, preco, estoque))
                conn.commit()
        except sqlite3.IntegrityError:
            return "<p>Produto já cadastrado.</p>"
        backup_db()
        return redirect(url_for('index'))
    
    return render_template('cadastrar_produto.html')

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO clientes (nome) VALUES (?)", (nome,))
                conn.commit()
        except sqlite3.IntegrityError:
            return "<p>Cliente já cadastrado.</p>"
        backup_db()
        return redirect(url_for('index'))
    
    return render_template('cadastrar_cliente.html')

@app.route('/listar_produtos')
def listar_produtos():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, preco, estoque FROM produtos")
        produtos = cursor.fetchall()
    return render_template('listar_produtos.html', produtos=produtos)

@app.route('/listar_clientes')
def listar_clientes():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM clientes")
        clientes = [row[0] for row in cursor.fetchall()]
    return render_template('listar_clientes.html', clientes=clientes)

@app.route('/realizar_venda', methods=['GET', 'POST'])
def realizar_venda():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, nome FROM clientes")
        clientes = cursor.fetchall()

        cursor.execute("SELECT id, nome, preco, estoque FROM produtos")
        produtos_rows = cursor.fetchall()
        produtos = [{"id": pid, "nome": pname, "preco": ppreco, "estoque": pestoque} for pid, pname, ppreco, pestoque in produtos_rows]

        if not produtos or not clientes:
            return "<p>É necessário cadastrar produtos e clientes antes de realizar uma venda.</p>"

        if request.method == 'POST':
            cliente_id = int(request.form['cliente'])
            produto_id = int(request.form['produto'])
            quantidade = int(request.form['quantidade'])
            ajuste = float(request.form.get('ajuste', 0))
            forma_pagamento = request.form['forma_pagamento']

            cursor.execute("SELECT preco, estoque FROM produtos WHERE id=?", (produto_id,))
            preco_row = cursor.fetchone()
            if not preco_row:
                return "<p>Produto não encontrado.</p>"
            preco, estoque_atual = preco_row

            if quantidade > estoque_atual:
                return "<p>Quantidade insuficiente em estoque.</p>"

            total = quantidade * preco + ajuste

            cursor.execute("""
                INSERT INTO vendas (cliente_id, produto_id, quantidade, total, forma_pagamento)
                VALUES (?, ?, ?, ?, ?)
            """, (cliente_id, produto_id, quantidade, total, forma_pagamento))

            novo_estoque = estoque_atual - quantidade
            cursor.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo_estoque, produto_id))

            conn.commit()
            backup_db()
            return redirect(url_for('cupom_fiscal', venda_id=cursor.lastrowid))

    return render_template('realizar_venda.html', clientes=clientes, produtos=produtos)

@app.route('/cupom_fiscal/<int:venda_id>')
def cupom_fiscal(venda_id):
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nome, p.nome, p.preco, v.quantidade, v.total, v.forma_pagamento
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.id=?
        """, (venda_id,))
        row = cursor.fetchone()
        if not row:
            return "<p>Venda não encontrada.</p>"
        _, cliente, produto_nome, preco, quantidade, total, forma_pagamento = row
        venda = {
            "cliente": cliente,
            "produto": produto_nome,
            "quantidade": quantidade,
            "preco": preco,
            "total": total,
            "forma_pagamento": forma_pagamento
        }
    return render_template('cupom_fiscal.html', venda=venda)

@app.route('/cupom_fiscal/<int:venda_id>.pdf')
def cupom_pdf(venda_id):
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    from weasyprint import HTML # type: ignore
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nome, p.nome, p.preco, v.quantidade, v.total, v.forma_pagamento
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.id=?
        """, (venda_id,))
        row = cursor.fetchone()
        if not row:
            return "<p>Venda nao encontrada.</p>"
        _, cliente, produto_nome, preco, quantidade, total, forma_pagamento = row
        venda = {
            "cliente": cliente,
            "produto": produto_nome,
            "quantidade": quantidade,
            "preco": preco,
            "total": total,
            "forma_pagamento": forma_pagamento
        }

    html_content = render_template('cupom_fiscal.html', venda=venda)
    pdf = HTML(string=html_content).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=cupom_{venda_id}.pdf'
    return response

@app.route('/historico_vendas')
def historico_vendas():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nome, p.nome, v.quantidade, v.total, v.forma_pagamento, v.data_venda
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN produtos p ON v.produto_id = p.id
            ORDER BY v.id DESC
        """)
        rows = cursor.fetchall()
        vendas = [{
            "id": r[0],
            "cliente": r[1],
            "produto": r[2],
            "quantidade": r[3],
            "total": r[4],
            "forma_pagamento": r[5],
            "data_venda": r[6]
        } for r in rows]
    return render_template('historico_vendas.html', vendas=vendas)

@app.route('/relatorios')
def relatorios():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DATE(data_venda), SUM(total) FROM vendas GROUP BY DATE(data_venda) ORDER BY DATE(data_venda) DESC")
        dados_diarios = cursor.fetchall()

        cursor.execute("SELECT SUM(total) FROM vendas")
        total_geral = cursor.fetchone()[0] or 0.0

    return render_template('relatorios.html',
                           dados_diarios=dados_diarios,
                           total_geral=total_geral)

@app.route('/api/produtos')
def api_produtos():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco, estoque FROM produtos")
        rows = cursor.fetchall()
        produtos = [{"id": r[0], "nome": r[1], "preco": r[2], "estoque": r[3]} for r in rows]
        return jsonify(produtos)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)