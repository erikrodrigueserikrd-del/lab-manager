import sqlite3
import os

def configurar_arquivos():
    # --- PARTE 1: CRIAR AS PASTAS FÍSICAS ---
    # Define o caminho: pasta atual -> static -> uploads
    caminho_static = 'static'
    caminho_uploads = os.path.join(caminho_static, 'uploads')

    # Cria a pasta 'static' se não existir
    if not os.path.exists(caminho_static):
        os.makedirs(caminho_static)
        print("✅ Pasta 'static' criada.")

    # Cria a pasta 'uploads' se não existir
    if not os.path.exists(caminho_uploads):
        os.makedirs(caminho_uploads)
        print("✅ Pasta 'static/uploads' criada.")
    else:
        print("ℹ️ Pasta 'static/uploads' já existia.")

    # --- PARTE 2: CRIAR A TABELA NO BANCO ---
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    # Criamos a tabela 'articles' vinculada à tabela 'experiments'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id),
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tabela 'articles' criada no banco de dados!")

if __name__ == "__main__":
    configurar_arquivos()