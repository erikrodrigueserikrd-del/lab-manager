import sqlite3

def atualizar_banco():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    # Criar tabela de Experimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'planejamento',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tabela 'experiments' adicionada com sucesso!")

if __name__ == "__main__":
    atualizar_banco()