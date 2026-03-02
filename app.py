import sqlite3
import json
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('fiesta_v2.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS amigos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            peso INTEGER DEFAULT 70,
            sexo TEXT DEFAULT 'H',
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
    conn = sqlite3.connect('fiesta_v2.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- LÓGICA CLÍNICA EXACTA ---
def calcular_estado(cervezas, cubatas, chupitos, peso, sexo):
    gramos_alcohol = (cervezas * 13) + (cubatas * 16) + (chupitos * 10)
    factor = 0.68 if sexo == 'H' else 0.55
    peso_real = peso if peso > 0 else 70 
    
    bac_estimado = gramos_alcohol / (peso_real * factor)
    
    if bac_estimado < 0.25: return 'Sobrio'
    elif bac_estimado < 0.60: return 'Puntillo'
    elif bac_estimado < 1.50: return 'Borracho'
    else: return 'Ebrio'

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
            --accent: #ff4757; --success: #2ed573; --minus-btn: #575775;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        
        .dashboard { display: flex; justify-content: space-between; background: var(--card-bg); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .stat-box { text-align: center; width: 30%; }
        .stat-box span { display: block; font-size: 24px; font-weight: bold; }
        .stat-box small { color: var(--text-muted); font-size: 12px; text-transform: uppercase; }

        .card { background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        input[type="text"], input[type="number"], select { padding: 12px; border-radius: 8px; border: none; background: var(--input-bg); color: white; box-sizing: border-box; }
        button.btn-main { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--success); color: white; font-weight: bold; cursor: pointer; margin-top: 10px; }
        
        .amigo-card { background: var(--input-bg); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #ccc; transition: all 0.3s ease; }
        .amigo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
        .amigo-nombre { font-size: 1.2em; font-weight: bold; display: flex; align-items: center; gap: 8px; }
        .amigo-datos { font-size: 0.8em; color: var(--text-muted); font-weight: normal; }
        .badge-hora { background: #000; padding: 4px 8px; border-radius: 12px; font-size: 11px; color: var(--text-muted); }
        
        .estado-label { font-size: 0.95em; margin-bottom: 15px; font-style: italic; color: #ccc; transition: 0.3s; }
        
        .controles-bebidas { display: flex; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; }
        .bebida-item { display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 1.1em; width: 30%; }
        
        .botones-accion { display: flex; gap: 5px; }
        .btn-plus, .btn-minus { color: white; border: none; border-radius: 5px; width: 32px; height: 32px; font-size: 18px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; transition: transform 0.1s;}
        .btn-plus { background: var(--accent); }
        .btn-minus { background: var(--minus-btn); }
        .btn-plus:active, .btn-minus:active { transform: scale(0.85); }
        
        .estado-Sobrio { border-color: var(--success); }
        .estado-Puntillo { border-color: #1e90ff; }
        .estado-Borracho { border-color: #ffa502; }
        .estado-Ebrio { border-color: var(--accent); }
    </style>
</head>
<body>

<div class="container">
    <h2 style="text-align: center; margin-bottom: 5px;">Party Tracker Pro 🍻</h2>
    <p style="text-align: center; color: var(--text-muted); margin-top: 0; margin-bottom: 20px;">Sin recargas (AJAX) ⚡</p>

    <div class="dashboard">
        <div class="stat-box"><span id="dash-cervezas">{{ totales.cervezas }}</span><small>Cervezas</small></div>
        <div class="stat-box"><span id="dash-cubatas">{{ totales.cubatas }}</span><small>Cubatas</small></div>
        <div class="stat-box"><span id="dash-chupitos">{{ totales.chupitos }}</span><small>Chupitos</small></div>
    </div>

    {% if nombres_json != '[]' %}
    <div class="card">
        <h3 style="margin-top:0; border-bottom: 1px solid #333; padding-bottom: 10px;">🏆 Ranking de Aguante</h3>
        <canvas id="rankingChart"></canvas>
    </div>
    {% endif %}

    <div class="card">
        <form method="POST" action="/agregar" style="margin: 0; display: flex; flex-direction: column; gap: 10px;">
            <input type="text" name="nombre" required placeholder="Nombre del amigo..." style="width: 100%;">
            <div style="display: flex; gap: 10px;">
                <input type="number" name="peso" required placeholder="Peso (kg)" value="70" min="40" max="150" style="width: 50%;">
                <select name="sexo" style="width: 50%;">
                    <option value="H">Hombre</option>
                    <option value="M">Mujer</option>
                </select>
            </div>
            <button type="submit" class="btn-main">➕ Añadir a la fiesta</button>
        </form>
    </div>

    {% if amigos|length == 0 %}
        <p style="text-align: center; color: var(--text-muted);">Aún no hay nadie en la fiesta.</p>
    {% else %}
        {% for a in amigos %}
        <div id="card-{{ a['id'] }}" class="amigo-card estado-{{ a['estado'] }}">
            <div class="amigo-header">
                <span class="amigo-nombre">
                    {{ a['nombre'] }} 
                    <span class="amigo-datos">({{ a['peso'] }}kg, {{ a['sexo'] }})</span>
                    <span id="medalla-{{ a['id'] }}">
                        {% set total_b = a['cervezas'] + a['cubatas'] + a['chupitos'] %}
                        {% if total_b > 0 and total_b == max_bebidas %} 👑
                        {% elif total_b == 0 %} 💧
                        {% endif %}
                    </span>
                </span>
                <span id="hora-{{ a['id'] }}" class="badge-hora">Últ. act: {{ a['hora'] }}</span>
            </div>
            
            <div id="estado-label-{{ a['id'] }}" class="estado-label">
                {% if a['estado'] == 'Sobrio' %} Fresquísimo / Sobrio 💧
                {% elif a['estado'] == 'Puntillo' %} Con el puntillo alegre 🕺
                {% elif a['estado'] == 'Borracho' %} Borracho / Perdiendo los papeles 🥴
                {% elif a['estado'] == 'Ebrio' %} Ebrio Extremo 💀
                {% endif %}
            </div>
            
            <div class="controles-bebidas">
                <div class="bebida-item">
                    <span id="count-cervezas-{{ a['id'] }}">{{ a['cervezas'] }} 🍺</span>
                    <div class="botones-accion">
                        <button class="btn-minus" onclick="actualizarBebida({{ a['id'] }}, 'cervezas', 'restar')">-</button>
                        <button class="btn-plus" onclick="actualizarBebida({{ a['id'] }}, 'cervezas', 'sumar')">+</button>
                    </div>
                </div>
                <div class="bebida-item">
                    <span id="count-cubatas-{{ a['id'] }}">{{ a['cubatas'] }} 🍹</span>
                    <div class="botones-accion">
                        <button class="btn-minus" onclick="actualizarBebida({{ a['id'] }}, 'cubatas', 'restar')">-</button>
                        <button class="btn-plus" onclick="actualizarBebida({{ a['id'] }}, 'cubatas', 'sumar')">+</button>
                    </div>
                </div>
                <div class="bebida-item">
                    <span id="count-chupitos-{{ a['id'] }}">{{ a['chupitos'] }} 🥃</span>
                    <div class="botones-accion">
                        <button class="btn-minus" onclick="actualizarBebida({{ a['id'] }}, 'chupitos', 'restar')">-</button>
                        <button class="btn-plus" onclick="actualizarBebida({{ a['id'] }}, 'chupitos', 'sumar')">+</button>
                    </div>
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
    // Inicializar Gráfico
    const nombres = {{ nombres_json | safe }};
    if (nombres.length > 0) {
        const ctx = document.getElementById('rankingChart').getContext('2d');
        window.miGrafico = new Chart(ctx, {
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
                plugins: { legend: { labels: { color: '#ffffff' } } },
                animation: { duration: 400 } // Animación más rápida para las actualizaciones
            }
        });
    }

    // Función que se ejecuta al darle al + o al -
    function actualizarBebida(id, bebida, operacion) {
        // Enviar petición invisible a Python
        fetch('/api/bebida', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, bebida: bebida, operacion: operacion })
        })
        .then(response => response.json())
        .then(data => {
            // 1. Actualizar números del amigo
            const emojis = { 'cervezas': '🍺', 'cubatas': '🍹', 'chupitos': '🥃' };
            document.getElementById('count-' + bebida + '-' + id).innerText = data.amigo[bebida] + ' ' + emojis[bebida];
            document.getElementById('hora-' + id).innerText = 'Últ. act: ' + data.amigo.hora;
            
            // 2. Actualizar colores y texto de estado
            document.getElementById('card-' + id).className = 'amigo-card estado-' + data.amigo.estado;
            const textosEstado = {
                'Sobrio': 'Fresquísimo / Sobrio 💧',
                'Puntillo': 'Con el puntillo alegre 🕺',
                'Borracho': 'Borracho / Perdiendo los papeles 🥴',
                'Ebrio': 'Ebrio Extremo 💀'
            };
            document.getElementById('estado-label-' + id).innerText = textosEstado[data.amigo.estado];

            // 3. Actualizar Dashboard General
            document.getElementById('dash-cervezas').innerText = data.totales.cervezas;
            document.getElementById('dash-cubatas').innerText = data.totales.cubatas;
            document.getElementById('dash-chupitos').innerText = data.totales.chupitos;

            // 4. Actualizar Medallas de TODOS los amigos
            data.amigos_estados.forEach(amigo => {
                let medallaEl = document.getElementById('medalla-' + amigo.id);
                if (medallaEl) {
                    if (amigo.total > 0 && amigo.total === data.max_bebidas) {
                        medallaEl.innerText = ' 👑';
                    } else if (amigo.total === 0) {
                        medallaEl.innerText = ' 💧';
                    } else {
                        medallaEl.innerText = '';
                    }
                }
            });

            // 5. Actualizar Gráfico en vivo
            if (window.miGrafico) {
                window.miGrafico.data.labels = data.ranking.nombres;
                window.miGrafico.data.datasets[0].data = data.ranking.cervezas;
                window.miGrafico.data.datasets[1].data = data.ranking.cubatas;
                window.miGrafico.data.datasets[2].data = data.ranking.chupitos;
                window.miGrafico.update();
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
    max_bebidas = max([(a['cervezas'] + a['cubatas'] + a['chupitos']) for a in amigos]) if amigos else 0
    
    totales = conn.execute('SELECT SUM(cervezas) as cervezas, SUM(cubatas) as cubatas, SUM(chupitos) as chupitos FROM amigos').fetchone()
    totales_dict = {
        'cervezas': totales['cervezas'] or 0, 'cubatas': totales['cubatas'] or 0, 'chupitos': totales['chupitos'] or 0
    }
    
    top_query = 'SELECT nombre, cervezas, cubatas, chupitos FROM amigos ORDER BY (cervezas + cubatas + chupitos) DESC'
    top_amigos = conn.execute(top_query).fetchall()
    
    nombres_lista = [a['nombre'] for a in top_amigos]
    cervezas_lista = [a['cervezas'] for a in top_amigos]
    cubatas_lista = [a['cubatas'] for a in top_amigos]
    chupitos_lista = [a['chupitos'] for a in top_amigos]
    
    conn.close()
    
    return render_template_string(HTML, 
                                  amigos=amigos, max_bebidas=max_bebidas, totales=totales_dict,
                                  nombres_json=json.dumps(nombres_lista), cervezas_json=json.dumps(cervezas_lista),
                                  cubatas_json=json.dumps(cubatas_lista), chupitos_json=json.dumps(chupitos_lista))

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre'].strip()
    peso = int(request.form.get('peso', 70))
    sexo = request.form.get('sexo', 'H')
    hora_actual = datetime.now().strftime("%H:%M")
    
    if nombre:
        conn = get_db()
        try:
            conn.execute('INSERT INTO amigos (nombre, peso, sexo, hora, estado) VALUES (?, ?, ?, ?, ?)', 
                         (nombre, peso, sexo, hora_actual, 'Sobrio'))
            conn.commit()
        except sqlite3.IntegrityError:
            pass 
        finally:
            conn.close()
    return redirect(url_for('index'))

# ¡NUEVA RUTA API INVISIBLE PARA JAVASCRIPT!
@app.route('/api/bebida', methods=['POST'])
def api_bebida():
    datos = request.get_json()
    amigo_id = datos['id']
    bebida = datos['bebida']
    operacion = datos['operacion'] # 'sumar' o 'restar'
    hora_actual = datetime.now().strftime("%H:%M")
    
    conn = get_db()
    amigo = conn.execute('SELECT cervezas, cubatas, chupitos, peso, sexo FROM amigos WHERE id = ?', (amigo_id,)).fetchone()
    
    c, cu, ch = amigo['cervezas'], amigo['cubatas'], amigo['chupitos']
    peso, sexo = amigo['peso'], amigo['sexo']
    
    # Aplicar la suma o la resta
    if operacion == 'sumar':
        if bebida == 'cervezas': c += 1
        elif bebida == 'cubatas': cu += 1
        elif bebida == 'chupitos': ch += 1
    elif operacion == 'restar':
        if bebida == 'cervezas' and c > 0: c -= 1
        elif bebida == 'cubatas' and cu > 0: cu -= 1
        elif bebida == 'chupitos' and ch > 0: ch -= 1
        
    nuevo_estado = calcular_estado(c, cu, ch, peso, sexo)
    nueva_cantidad = c if bebida == 'cervezas' else (cu if bebida == 'cubatas' else ch)
    
    # Actualizar en BD
    conn.execute(f'UPDATE amigos SET {bebida} = ?, estado = ?, hora = ? WHERE id = ?', (nueva_cantidad, nuevo_estado, hora_actual, amigo_id))
    conn.commit()
    
    # Recopilar todos los datos nuevos para enviárselos de vuelta a Javascript
    amigos_todos = conn.execute('SELECT * FROM amigos').fetchall()
    max_bebidas = max([(a['cervezas'] + a['cubatas'] + a['chupitos']) for a in amigos_todos]) if amigos_todos else 0
    totales = conn.execute('SELECT SUM(cervezas) as c, SUM(cubatas) as cu, SUM(chupitos) as ch FROM amigos').fetchone()
    top_amigos = conn.execute('SELECT nombre, cervezas, cubatas, chupitos FROM amigos ORDER BY (cervezas + cubatas + chupitos) DESC').fetchall()
    conn.close()
    
    # Devolvemos un paquete de datos JSON
    return jsonify({
        'amigo': {'cervezas': c, 'cubatas': cu, 'chupitos': ch, 'estado': nuevo_estado, 'hora': hora_actual},
        'totales': {'cervezas': totales['c'] or 0, 'cubatas': totales['cu'] or 0, 'chupitos': totales['ch'] or 0},
        'ranking': {
            'nombres': [a['nombre'] for a in top_amigos],
            'cervezas': [a['cervezas'] for a in top_amigos],
            'cubatas': [a['cubatas'] for a in top_amigos],
            'chupitos': [a['chupitos'] for a in top_amigos]
        },
        'amigos_estados': [{'id': a['id'], 'total': a['cervezas'] + a['cubatas'] + a['chupitos']} for a in amigos_todos],
        'max_bebidas': max_bebidas
    })

@app.route('/resetear', methods=['POST'])
def resetear():
    conn = get_db()
    conn.execute('DELETE FROM amigos')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
