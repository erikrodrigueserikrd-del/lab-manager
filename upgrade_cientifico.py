import sqlite3

def upgrade_schema():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    print("🔬 Iniciando atualização do Schema Científico...")

    # 1. ATUALIZAR EXPERIMENTOS (Metadata Ambiental)
    # Adiciona colunas para temperatura, fotoperíodo, meio de cultura, etc.
    cols_experiments = ["temperature", "photoperiod", "culture_media", "strain_info"]
    for col in cols_experiments:
        try:
            cursor.execute(f"ALTER TABLE experiments ADD COLUMN {col} TEXT")
            print(f"   -> Coluna '{col}' adicionada em 'experiments'.")
        except:
            pass # Coluna já existe

    # 2. ATUALIZAR TAREFAS (Prazos e SOPs)
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATE")
        cursor.execute("ALTER TABLE tasks ADD COLUMN sop_instructions TEXT")
        print("   -> Colunas de Prazo e SOP adicionadas em 'tasks'.")
    except:
        pass

    # 3. TABELA DE TRATAMENTOS (Ex: Controle, Co-inoculação)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id)
        )
    ''')

    # 4. TABELA DE VARIÁVEIS DE RESPOSTA (Ex: Clorofila-a, pH)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            unit TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id)
        )
    ''')

    # 5. TABELA DE RÉPLICAS/UNIDADES EXPERIMENTAIS (Ex: EXP27-T01-R01)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            treatment_id INTEGER,
            name TEXT NOT NULL,
            qr_code TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id),
            FOREIGN KEY (treatment_id) REFERENCES treatments (id)
        )
    ''')

    # 6. TABELA DE PONTOS DE DADOS (A Matriz de Coleta)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            replica_id INTEGER NOT NULL,
            variable_id INTEGER NOT NULL,
            timepoint TEXT NOT NULL, -- Ex: T0, T7, T48
            value REAL,
            measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (replica_id) REFERENCES replicas (id),
            FOREIGN KEY (variable_id) REFERENCES variables (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Banco de Dados atualizado com sucesso!")

if __name__ == "__main__":
    upgrade_schema()