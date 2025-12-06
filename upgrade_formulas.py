import sqlite3

def upgrade_formulas():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    print("⚗️ Atualizando Banco para Suporte a Fórmulas...")

    # 1. Tabela de Fórmulas
    # expression: A equação matemática (ex: "[Leitura 665] - [Leitura 750]")
    # target_variable_id: Onde o resultado será escrito (ex: ID da coluna Clorofila)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            name TEXT,
            target_variable_id INTEGER NOT NULL,
            expression TEXT NOT NULL,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id),
            FOREIGN KEY (target_variable_id) REFERENCES variables (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tabela 'formulas' criada com sucesso!")

if __name__ == "__main__":
    upgrade_formulas()