import sqlite3
import hashlib

# 1. Cria o banco de dados e a tabela se não existirem
def inicializar_db():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados verificado/criado com sucesso.")

# 2. Pergunta os dados e cria o usuário
def criar_login():
    print("\n--- CRIAR NOVO USUÁRIO ---")
    usuario = input("Digite o nome de usuário (ex: joao.silva): ")
    senha = input("Digite a senha para este usuário: ")

    # Criptografa a senha antes de salvar
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    try:
        conn = sqlite3.connect('dados.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (usuario, senha_hash))
        conn.commit()
        print(f"✅ Sucesso! O usuário '{usuario}' foi criado e já pode fazer login.")
    except sqlite3.IntegrityError:
        print(f"❌ Erro: O usuário '{usuario}' já existe.")
    finally:
        conn.close()

if __name__ == "__main__":
    inicializar_db()
    criar_login()