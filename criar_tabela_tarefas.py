import sqlite3

def criar_tabela():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    # Cria a tabela de tarefas vinculada aos experimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            priority TEXT DEFAULT 'media',
            status TEXT DEFAULT 'pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tabela 'tasks' criada com sucesso!")

if __name__ == "__main__":
    criar_tabela()