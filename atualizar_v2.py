import sqlite3

def adicionar_datas():
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    try:
        # Tenta adicionar as colunas. Se já existirem, vai dar erro e ignoramos.
        cursor.execute("ALTER TABLE experiments ADD COLUMN start_date DATE")
        cursor.execute("ALTER TABLE experiments ADD COLUMN deadline DATE")
        conn.commit()
        print("✅ Colunas de data adicionadas com sucesso!")
    except sqlite3.OperationalError:
        print("⚠️ As colunas provavelmente já existem.")
    
    conn.close()

if __name__ == "__main__":
    adicionar_datas()