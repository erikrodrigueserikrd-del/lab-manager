import sqlite3

def upgrade_universal():
    conn = sqlite3.connect('dados.db')
    print("🌍 Criando tabela de Fórmulas Universais...")

    # Tabela para guardar fórmulas que servem para TODOS os experimentos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS global_formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            expression TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Sucesso! Tabela 'global_formulas' pronta.")

if __name__ == "__main__":
    upgrade_universal()