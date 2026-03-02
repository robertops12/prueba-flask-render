import sqlite3
import json
from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('fiesta.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS amigos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            cervezas INTEGER DEFAULT 0,
            cubatas INTEGER DEFAULT 0,
            chupitos INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'Sobrio',
            hora TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('fiesta.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- LÓGICA DE EMBRIAGUEZ AUTOMÁTICA ---
def calcular_estado(cervezas, cubatas, chupitos):
    # Sistema de puntos: Cerveza (1), Cubata (2), Chupito (1)
    puntos = (cervezas * 1) + (cubatas * 2) + (chupitos * 1)
    
    if puntos == 0:
        return 'Sobrio'
    elif puntos <= 3:
        return 'Puntillo'
    elif puntos <= 7:
        return 'Borracho'
    else:
        return 'Ebrio'

# --- DISEÑO DE LA APLICACIÓN ---
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Party Tracker Pro DB 🍻</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #12121c; --card-bg: #1e1e2f; --input-bg: #2a2a40;
            --text-main: #ffffff; --text-muted: #a0a0b5;
            --accent: #ff4757; --success: #2ed573;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        
        .dashboard { display: flex; justify-content: space-between; background: var(--card-bg); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .stat-box { text-align: center; width: 30%; }
        .stat-box span { display: block; font-size: 24px; font-weight: bold; }
        .stat-box small { color: var(--text-muted); font-size: 12px; text-transform: uppercase; }

        .card { background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--input-bg); color: white; margin-bottom: 10px; box-sizing: border-box; }
        button.btn-main { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--success); color: white; font-weight: bold; cursor: pointer; }
        
        .amigo-card { background: var(--input-bg); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #ccc; transition: 0.3s; }
        .amigo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
        .amigo-nombre { font-size: 1.2em; font-weight: bold; }
        .badge-hora { background: #000; padding: 4px 8px; border-radius: 12px; font-size: 11px; color: var(--text-muted); }
        
        .estado-label { font-size: 0.95em; margin-bottom: 15px; font-style: italic; color: #ccc; }
        
        .controles-bebidas { display: flex; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; }
        .bebida-item { display: flex; align-items: center; gap: 8px; font-size: 1.1em; }
        .btn-plus { background: var(--accent); color: white; border: none; border-radius: 5px; width: 30px; height: 30px; font-size: 18px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; }
        .btn-plus:active { transform: scale(0.9); }
        
        .estado-Sobrio { border-color: var(--success); }
        .estado-Puntillo { border-color: #1e90ff; }
        .estado-Borracho { border-color: #ffa502; }
        .estado-Ebrio { border-color: var(--accent); }
    </style>
</head>
<body>

<div class="container">
    <h2 style="text-align: center; margin-bottom: 5px;">Party Tracker Pro 🍻</h2>
    <p style="text-align: center; color: var(--text-muted); margin-top: 0; margin-bottom: 20px;">Cálculo Automático de Estado</p>

    <div class="dashboard">
        <div class="stat-box"><span>{{ totales.cervezas }}</span><small>Cervezas</small></div>
        <div class="stat-box"><span>{{ totales.cubatas }}</span><small>Cubatas</small></div>
        <div class="stat-box"><span>{{ totales.chupitos }}</span><small>Chupitos</small></div>
    </div>

    {% if nombres_json != '[]' %}
    <div class="card">
        <h3 style="margin-top:0; border-bottom: 1px solid #333; padding-bottom: 10px;">🏆 Ranking de Aguante</h3>
        <canvas id="rankingChart"></canvas>
    </div>
    {% endif %}

    <div class="card">
        <form method="POST" action="/agregar" style="margin: 0;">
            <input type="text" name="nombre" required placeholder="Nombre del nuevo amigo...">
            <button type="submit" class="btn-main">➕ Añadir a la fiesta</button>
        </form>
    </div>

    {% if amigos|length == 0 %}
        <p style="text-align: center; color: var(--text-muted);">Aún no hay nadie en la fiesta.</p>
    {% else %}
        {% for a in amigos %}
        <div class="amigo-card estado-{{ a['estado'] }}">
            <div class="amigo-header">
                <span class="amigo-nombre">{{ a['nombre'] }}</span>
                <span class="badge-hora">Últ. act: {{ a['hora'] }}</span>
            </div>
            
            <div class="estado-label">
                {% if a['estado'] == 'Sobrio' %} Fresquísimo / Sobrio 💧
                {% elif a['estado'] == 'Puntillo' %} Con el puntillo alegre 🕺
                {% elif a['estado'] == 'Borracho' %} Borracho / Perdiendo los papeles 🥴
                {% elif a['estado'] == 'Ebrio' %} Ebrio Extremo 💀
                {% endif %}
            </div>
            
            <div class="controles-bebidas">
                <div class="bebida-item">
                    {{ a['cervezas'] }} 🍺
                    <form method="POST" action="/sumar" style="margin:0;"><input type="hidden" name="id" value="{{ a['id'] }}"><input type="hidden" name="bebida" value="cervezas"><button type="submit" class="btn-plus">+</button></form>
                </div>
                <div class="bebida-item">
                    {{ a['cubatas'] }} 🍹
                    <form method="POST" action="/sumar" style="margin:0;"><input type="hidden" name="id" value="{{ a['id'] }}"><input type="hidden" name="bebida" value="cubatas"><button type="submit" class="btn-plus">+</button></form>
                </div>
                <div class="bebida-item">
                    {{ a['chupitos'] }} 🥃
                    <form method="POST" action="/sumar" style="margin:0;"><input type="hidden" name="id" value="{{ a['id'] }}"><input type="hidden" name="bebida" value="chupitos"><button type="submit" class="btn-plus">+</button></form>
                </div>
            </div>
        </div>
        {% endfor %}
    {% endif %}

    <div style="margin-top: 40px; text-align: center;">
        <form method="POST" action="/resetear" onsubmit="return confirm('¿Seguro que quieres borrar toda la base de datos?');">
            <button type="submit" style="background: transparent; border: 1px solid var(--accent); color: var(--accent); padding: 10px; border-radius: 5px; cursor: pointer;">🧹 Borrar Base de Datos</button>
        </form>
    </div>
</div>

<script>
    const nombres = {{ nombres_json | safe }};
    if (nombres.length > 0) {
        const ctx = document.getElementById('rankingChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: nombres,
                datasets: [
                    { label: '🍺 Cervezas', data: {{ cervezas_json | safe }}, backgroundColor: '#f1c40f' },
                    { label: '🍹 Cubatas', data: {{ cubatas_json | safe }}, backgroundColor: '#e74c3c' },
                    { label: '🥃 Chupitos', data: {{ chupitos_json | safe }}, backgroundColor: '#e67e22' }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { stacked: true, ticks: { color: '#a0a0b5' }, grid: { color: '#333' } },
                    y: { stacked: true, beginAtZero: true, ticks: { color: '#a0a0b5', stepSize: 1 }, grid: { color: '#333' } }
                },
                plugins: { legend: { labels: { color: '#ffffff' } } }
            }
        });
    }
</script>

</body>
</html>
"""

# --- RUTAS ---
@app.route('/')
def index():
    conn = get_db()
    amigos = conn.execute('SELECT * FROM amigos ORDER BY hora DESC').fetchall()
    
    totales = conn.execute('SELECT SUM(cervezas) as cervezas, SUM(cubatas) as cubatas, SUM(chupitos) as chupitos FROM amigos').fetchone()
    totales_dict = {
        'cervezas': totales['cervezas'] or 0,
        'cubatas': totales['cubatas'] or 0,
        'chupitos': totales['chupitos'] or 0
    }
    
    top_query = 'SELECT nombre, cervezas, cubatas, chupitos FROM amigos ORDER BY (cervezas + cubatas + chupitos) DESC'
    top_amigos = conn.execute(top_query).fetchall()
    
    nombres_lista = [a['nombre'] for a in top_amigos]
    cervezas_lista = [a['cervezas'] for a in top_amigos]
    cubatas_lista = [a['cubatas'] for a in top_amigos]
    chupitos_lista = [a['chupitos'] for a in top_amigos]
    
    conn.close()
    
    return render_template_string(HTML, 
                                  amigos=amigos, 
                                  totales=totales_dict,
                                  nombres_json=json.dumps(nombres_lista),
                                  cervezas_json=json.dumps(cervezas_lista),
                                  cubatas_json=json.dumps(cubatas_lista),
                                  chupitos_json=json.dumps(chupitos_lista))

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre'].strip()
    hora_actual = datetime.now().strftime("%H:%M")
    if nombre:
        conn = get_db()
        try:
            # Por defecto, todos empiezan "Sobrios"
            conn.execute('INSERT INTO amigos (nombre, hora, estado) VALUES (?, ?, ?)', (nombre, hora_actual, 'Sobrio'))
            conn.commit()
        except sqlite3.IntegrityError:
            pass 
        finally:
            conn.close()
    return redirect(url_for('index'))

@app.route('/sumar', methods=['POST'])
def sumar():
    amigo_id = request.form['id']
    bebida = request.form['bebida'] 
    hora_actual = datetime.now().strftime("%H:%M")
    
    if bebida in ['cervezas', 'cubatas', 'chupitos']:
        conn = get_db()
        
        # 1. Obtenemos lo que llevaba bebido hasta ahora
        amigo = conn.execute('SELECT cervezas, cubatas, chupitos FROM amigos WHERE id = ?', (amigo_id,)).fetchone()
        c = amigo['cervezas']
        cu = amigo['cubatas']
        ch = amigo['chupitos']
        
        # 2. Le sumamos la bebida nueva que acaba de pulsar
        if bebida == 'cervezas': c += 1
        elif bebida == 'cubatas': cu += 1
        elif bebida == 'chupitos': ch += 1
        
        # 3. Calculamos automáticamente su nuevo nivel
        nuevo_estado = calcular_estado(c, cu, ch)
        
        # 4. Actualizamos la base de datos con la nueva bebida y el nuevo estado
        sql = f'UPDATE amigos SET {bebida} = ?, estado = ?, hora = ? WHERE id = ?'
        
        # Dependiendo de la bebida, pasamos la variable correcta al SQL
        nueva_cantidad = c if bebida == 'cervezas' else (cu if bebida == 'cubatas' else ch)
        
        conn.execute(sql, (nueva_cantidad, nuevo_estado, hora_actual, amigo_id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/resetear', methods=['POST'])
def resetear():
    conn = get_db()
    conn.execute('DELETE FROM amigos')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
