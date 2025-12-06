import csv
import io
from flask import Response # Importante para o download funcionar
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
import json # Importante para passar as fórmulas para o JavaScript

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def get_db_connection():
    conn = sqlite3.connect('dados.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ROTAS DE LOGIN/DASHBOARD (MANTIDAS IGUAIS) ---
@app.route('/', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (usuario,)).fetchone()
        conn.close()
        if user and user['password'] == senha_hash:
            session['usuario'] = user['username']
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            mensagem = 'Login incorreto!'
    return render_template('login.html', mensagem=mensagem)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', nome=session['usuario'])

@app.route('/experiments', methods=['GET', 'POST'])
def experiments():
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('INSERT INTO experiments (title, description, status, start_date, deadline, user_id) VALUES (?, ?, ?, ?, ?, ?)',
                     (request.form['title'], request.form['description'], request.form['status'], request.form['start_date'], request.form['deadline'], session['user_id']))
        conn.commit()
        return redirect(url_for('experiments'))
    
    experimentos = conn.execute("SELECT * FROM experiments ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('experiments.html', experimentos=experimentos)

# --- DETALHES DO EXPERIMENTO (ATUALIZADO COM FÓRMULAS) ---
@app.route('/experiment/<int:id>', methods=['GET', 'POST'])
def experiment_details(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    
    # Update Geral
    if request.method == 'POST' and 'update_experiment' in request.form:
        conn.execute('''UPDATE experiments SET title=?, description=?, status=?, start_date=?, deadline=?, temperature=?, photoperiod=?, culture_media=?, strain_info=? WHERE id = ?''', 
                     (request.form['title'], request.form['description'], request.form['status'], request.form['start_date'], request.form['deadline'], request.form['temperature'], request.form['photoperiod'], request.form['culture_media'], request.form['strain_info'], id))
        conn.commit()
        return redirect(url_for('experiment_details', id=id))

    # Carregamentos
    exp = conn.execute('SELECT * FROM experiments WHERE id = ?', (id,)).fetchone()
    if not exp: return "Erro", 404
    
    tarefas = conn.execute('SELECT * FROM tasks WHERE experiment_id = ? ORDER BY due_date ASC', (id,)).fetchall()
    artigos = conn.execute('SELECT * FROM articles WHERE experiment_id = ? ORDER BY created_at DESC', (id,)).fetchall()
    tratamentos = conn.execute('SELECT * FROM treatments WHERE experiment_id = ?', (id,)).fetchall()
    variaveis = conn.execute('SELECT * FROM variables WHERE experiment_id = ?', (id,)).fetchall()
    
    replicas = conn.execute('''SELECT r.*, t.name as treatment_name FROM replicas r LEFT JOIN treatments t ON r.treatment_id = t.id WHERE r.experiment_id = ? ORDER BY r.name''', (id,)).fetchall()
    
    # Matriz de Dados
    medicoes = conn.execute('SELECT * FROM measurements WHERE replica_id IN (SELECT id FROM replicas WHERE experiment_id = ?)', (id,)).fetchall()
    dados_matrix = {}
    for m in medicoes:
        if m['replica_id'] not in dados_matrix: dados_matrix[m['replica_id']] = {}
        dados_matrix[m['replica_id']][m['variable_id']] = m['value']

    # --- NOVO: CARREGAR FÓRMULAS ---
    # Precisamos do nome da variável alvo para o JS saber onde colocar o resultado
    formulas_db = conn.execute('''
        SELECT f.*, v.name as target_name 
        FROM formulas f 
        JOIN variables v ON f.target_variable_id = v.id 
        WHERE f.experiment_id = ?
    ''', (id,)).fetchall()
    
    # Converte para lista de dicionários para passar para o JavaScript via JSON
    formulas_list = [dict(f) for f in formulas_db]

    conn.close()
    
    return render_template('experiment_details.html', 
                           exp=exp, tasks=tarefas, articles=artigos,
                           treatments=tratamentos, variables=variaveis, 
                           replicas=replicas, matrix=dados_matrix,
                           formulas=formulas_list) # Passamos as fórmulas

# --- ROTAS CIENTÍFICAS ---

@app.route('/experiment/<int:id>/add_treatment', methods=['POST'])
def add_treatment(id):
    conn = get_db_connection()
    conn.execute('INSERT INTO treatments (experiment_id, name, description) VALUES (?, ?, ?)', (id, request.form['name'], request.form['description']))
    conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=id))

@app.route('/experiment/<int:id>/add_variable', methods=['POST'])
def add_variable(id):
    conn = get_db_connection()
    conn.execute('INSERT INTO variables (experiment_id, name, unit) VALUES (?, ?, ?)', (id, request.form['name'], request.form['unit']))
    conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=id))

# --- NOVO: DELETAR VARIÁVEL ---
@app.route('/variable/delete/<int:var_id>')
def delete_variable(var_id):
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    
    # 1. Descobrir ID do experimento para voltar depois
    var = conn.execute('SELECT experiment_id FROM variables WHERE id = ?', (var_id,)).fetchone()
    if var:
        exp_id = var['experiment_id']
        # 2. Apagar medições dessa variável (limpeza)
        conn.execute('DELETE FROM measurements WHERE variable_id = ?', (var_id,))
        # 3. Apagar fórmulas onde essa variável é o ALVO
        conn.execute('DELETE FROM formulas WHERE target_variable_id = ?', (var_id,))
        # 4. Apagar a variável
        conn.execute('DELETE FROM variables WHERE id = ?', (var_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('experiment_details', id=exp_id))
    
    conn.close()
    return redirect(url_for('dashboard'))

# --- NOVO: ADICIONAR FÓRMULA ---
@app.route('/experiment/<int:id>/add_formula', methods=['POST'])
def add_formula(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    
    target_id = request.form['target_variable_id']
    expression = request.form['expression'] # Ex: ([Leitura 665] - [Leitura 750]) * 10
    name = request.form['name']
    
    conn.execute('INSERT INTO formulas (experiment_id, name, target_variable_id, expression) VALUES (?, ?, ?, ?)',
                 (id, name, target_id, expression))
    conn.commit()
    conn.close()
    return redirect(url_for('experiment_details', id=id))

# --- NOVO: DELETAR FÓRMULA ---
@app.route('/formula/delete/<int:formula_id>')
def delete_formula(formula_id):
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    f = conn.execute('SELECT experiment_id FROM formulas WHERE id = ?', (formula_id,)).fetchone()
    if f:
        conn.execute('DELETE FROM formulas WHERE id = ?', (formula_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('experiment_details', id=f['experiment_id']))
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/experiment/<int:id>/generate_replicas', methods=['POST'])
def generate_replicas(id):
    conn = get_db_connection()
    t_id = request.form['treatment_id']
    num = int(request.form['num_replicas'])
    t_name = conn.execute('SELECT name FROM treatments WHERE id = ?', (t_id,)).fetchone()['name'][:3].upper()
    for i in range(1, num + 1):
        conn.execute('INSERT INTO replicas (experiment_id, treatment_id, name) VALUES (?, ?, ?)', (id, t_id, f"T-{t_name}-R{i:02d}"))
    conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=id))

@app.route('/experiment/<int:id>/save_data', methods=['POST'])
def save_data(id):
    conn = get_db_connection()
    for key, value in request.form.items():
        if key.startswith('valor_'):
            _, r_id, v_id = key.split('_')
            if value.strip() == '': continue
            exist = conn.execute('SELECT id FROM measurements WHERE replica_id=? AND variable_id=? AND timepoint="T48"', (r_id, v_id)).fetchone()
            if exist: conn.execute('UPDATE measurements SET value=? WHERE id=?', (value, exist['id']))
            else: conn.execute('INSERT INTO measurements (replica_id, variable_id, value, timepoint) VALUES (?, ?, ?, "T48")', (r_id, v_id, value))
    conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=id))

# --- TAREFAS/ARQUIVOS/DELETE ---
# (Mantive estas rotas compactadas pois não mudaram, mas estão aqui completas no código original)
@app.route('/task/add_complex/<int:experiment_id>', methods=['POST'])
def add_task_complex(experiment_id):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (experiment_id, title, priority, due_date, sop_instructions) VALUES (?, ?, ?, ?, ?)', 
                 (experiment_id, request.form['title'], request.form['priority'], request.form['due_date'], request.form['sop_instructions']))
    conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=experiment_id))

@app.route('/task/toggle/<int:task_id>')
def toggle_task(task_id):
    conn = get_db_connection(); t = conn.execute('SELECT status, experiment_id FROM tasks WHERE id=?', (task_id,)).fetchone()
    if t: conn.execute('UPDATE tasks SET status=? WHERE id=?', ('concluido' if t['status']=='pendente' else 'pendente', task_id)); conn.commit(); conn.close(); return redirect(url_for('experiment_details', id=t['experiment_id']))
    return redirect(url_for('dashboard'))

@app.route('/task/delete/<int:task_id>')
def delete_task(task_id):
    conn = get_db_connection(); t = conn.execute('SELECT experiment_id FROM tasks WHERE id=?', (task_id,)).fetchone()
    if t: conn.execute('DELETE FROM tasks WHERE id=?', (task_id,)); conn.commit(); conn.close(); return redirect(url_for('experiment_details', id=t['experiment_id']))
    return redirect(url_for('dashboard'))

@app.route('/experiment/<int:id>/upload', methods=['POST'])
def upload_experiment_file(id):
    f = request.files['file']
    if f and f.filename:
        n = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], n))
        conn = get_db_connection()
        conn.execute('INSERT INTO articles (title, filename, experiment_id, user_id) VALUES (?, ?, ?, ?)', (request.form['title'], n, id, session['user_id']))
        conn.commit(); conn.close()
    return redirect(url_for('experiment_details', id=id))

@app.route('/articles/delete/<int:id>')
def delete_article(id):
    conn = get_db_connection(); a = conn.execute('SELECT filename, experiment_id FROM articles WHERE id=?', (id,)).fetchone()
    if a:
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], a['filename']))
        except: pass
        conn.execute('DELETE FROM articles WHERE id=?', (id,)); conn.commit(); conn.close(); return redirect(url_for('experiment_details', id=a['experiment_id']))
    return redirect(url_for('dashboard'))

@app.route('/experiments/delete/<int:id>')
def delete_experiment(id):
    conn = get_db_connection()
    for table in ['tasks', 'articles', 'treatments', 'variables', 'replicas', 'formulas']: # Adicionado formulas no delete
        conn.execute(f'DELETE FROM {table} WHERE experiment_id = ?', (id,))
    conn.execute('DELETE FROM experiments WHERE id = ?', (id,))
    conn.commit(); conn.close()
    return redirect(url_for('experiments'))


    # --- ROTA DE EXPORTAÇÃO PARA CSV (NOVO) ---
@app.route('/experiment/<int:id>/export_csv')
def export_csv(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    
    # 1. Recuperar definições do experimento
    experimento = conn.execute('SELECT title FROM experiments WHERE id = ?', (id,)).fetchone()
    variaveis = conn.execute('SELECT * FROM variables WHERE experiment_id = ? ORDER BY id', (id,)).fetchall()
    replicas = conn.execute('''
        SELECT r.id, r.name, t.name as treatment_name 
        FROM replicas r 
        LEFT JOIN treatments t ON r.treatment_id = t.id 
        WHERE r.experiment_id = ? 
        ORDER BY r.name
    ''', (id,)).fetchall()
    
    # 2. Recuperar os dados (Medições)
    # Formato: dados[replica_id][variable_id] = valor
    medicoes = conn.execute('''
        SELECT replica_id, variable_id, value 
        FROM measurements 
        WHERE replica_id IN (SELECT id FROM replicas WHERE experiment_id = ?)
    ''', (id,)).fetchall()
    
    data_map = {}
    for m in medicoes:
        if m['replica_id'] not in data_map: data_map[m['replica_id']] = {}
        data_map[m['replica_id']][m['variable_id']] = m['value']
    
    conn.close()

    # 3. Construir o CSV na memória
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho: ID, Tratamento, [Nome Var 1], [Nome Var 2]...
    header = ['Codigo_Replica', 'Tratamento']
    var_ids = [] # Guardar a ordem dos IDs para preencher as linhas corretamente
    for v in variaveis:
        header.append(v['name'])
        var_ids.append(v['id'])
    
    writer.writerow(header)
    
    # Linhas de Dados
    for r in replicas:
        row = [r['name'], r['treatment_name']]
        
        # Preenche as colunas das variáveis
        for vid in var_ids:
            # Pega o valor ou deixa vazio se não existir
            valor = data_map.get(r['id'], {}).get(vid, '')
            # Troca ponto por vírgula se preferires Excel PT-BR, ou mantém ponto para R
            # Para o R, manter o PONTO é melhor.
            row.append(valor)
            
        writer.writerow(row)
    
    # 4. Preparar o arquivo para download
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=dados_experimento_{id}.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)