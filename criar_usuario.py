import sqlite3

DB_NAME = 'pdv.db'

def criar_usuario(nome, senha):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, senha) VALUES (?, ?)", (nome, senha))
            conn.commit()
            print(f"✅ Usuário '{nome}' criado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"❌ O nome '{nome}' já está em uso.")

if __name__ == '__main__':
    nome = input("Digite o nome do usuário: ")
    senha = input("Digite a senha: ")
    criar_usuario(nome, senha)