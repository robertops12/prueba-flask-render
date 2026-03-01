import sqlite3
from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('fiesta.db')
    c = conn.cursor()
    # Creamos la tabla si no existe
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

# Función auxiliar para conectarnos a la BD en cada petición
def get_db():
    conn = sqlite3.connect('fiesta.db')
    conn.row_factory = sqlite3.Row # Para poder acceder a las columnas por nombre
    return conn

# --- DISEÑO DE LA APLICACIÓN ---
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Party Tracker Pro DB 🍻</title>
    <style>
        :root {
            --bg-color: #12121c; --card-bg: #1e1e2f; --input-bg: #2a2a40;
            --text-main: #ffffff; --text-muted: #a0a0b5;
            --accent: #ff4757; --success: #2ed573;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        
        .dashboard { display: flex; justify-content: space-between; background: var(--card-bg); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .stat-box { text-align: center; width: 30%; }
        .stat-box span { display: block; font-size: 24px; font-weight: bold; }
        .stat-box small { color: var(--text-muted); font-size: 12px; text-transform: uppercase; }

        .card { background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--input-bg); color: white; margin-bottom: 10px; box-sizing: border-box; }
        button.btn-main { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--success); color: white; font-weight: bold; cursor: pointer; }
        
        .amigo-card { background: var(--input-bg); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #ccc; transition: 0.3s; }
        .amigo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .amigo-nombre { font-size: 1.2em; font-weight: bold; }
        .badge-hora { background: #000; padding: 4px 8px; border-radius: 12px; font-size: 11px; color: var(--text-muted); }
        
        /* Controles de bebida (+1) */
        .controles-bebidas { display: flex; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        .bebida-item { display: flex; align-items: center; gap: 8px; font-size: 1.1em; }
        .btn-plus { background: var(--accent); color: white; border: none; border-radius: 5px; width: 30px; height: 30px; font-size: 18px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; }
        .btn-plus:active { transform: scale(0.9); }
        
        select { width: 100%; padding: 10px; border-radius: 6px; border: none; background: #3e3e5c; color: white; font-size: 15px; cursor: pointer; }
        
        .estado-Sobrio { border-color: var(--success); }
        .estado-Puntillo { border-color: #1e90ff; }
        .estado-Borracho { border-color: #ffa502; }
        .estado-Ebrio { border-color: var(--accent); }
    </style>
</head>
<body>

<div class="container">
    <h2 style="text-align: center; margin-bottom: 5px;">Party Tracker Pro 🍻</h2>
    <p style="text-align: center; color: var(--text-muted); margin-top: 0; margin-bottom: 20px;">Base de Datos SQLite Activa</p>

    <div class="dashboard">
        <div class="stat-box"><span>{{ totales.cervezas }}</span><small>Cervezas</small></div>
        <div class="stat-box"><span>{{ totales.cubatas }}</span><small>Cubatas</small></div>
        <div class="stat-box"><span>{{ totales.chupitos }}</span><small>Chupitos</small></div>
    </div>

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

            <form method="POST" action="/estado" style="margin:0;">
                <input type="hidden" name="id" value="{{ a['id'] }}">
                <select name="estado" onchange="this.form.submit()">
                    <option value="Sobrio" {% if a['estado'] == 'Sobrio' %}selected{% endif %}>Fresquísimo / Sobrio 💧</option>
                    <option value="Puntillo" {% if a['estado'] == 'Puntillo' %}selected{% endif %}>Con el puntillo alegre 🕺</option>
                    <option value="Borracho" {% if a['estado'] == 'Borracho' %}selected{% endif %}>Borracho / Perdiendo los papeles 🥴</option>
                    <option value="Ebrio" {% if a['estado'] == 'Ebrio' %}selected{% endif %}>Ebrio Extremo 💀</option>
                </select>
            </form>
        </div>
        {% endfor %}
    {% endif %}

    <div style="margin-top: 40px; text-align: center;">
        <form method="POST" action="/resetear" onsubmit="return confirm('¿Seguro que quieres borrar toda la base de datos?');">
            <button type="submit" style="background: transparent; border: 1px solid var(--accent); color: var(--accent); padding: 10px; border-radius: 5px; cursor: pointer;">🧹 Borrar Base de Datos</button>
        </form>
    </div>
</div>

</body>
</html>
"""

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    conn = get_db()
    # Obtenemos todos los amigos ordenados por la última actualización
    amigos = conn.execute('SELECT * FROM amigos ORDER BY hora DESC').fetchall()
    
    # Calculamos los totales para el dashboard
    totales = conn.execute('SELECT SUM(cervezas) as cervezas, SUM(cubatas) as cubatas, SUM(chupitos) as chupitos FROM amigos').fetchone()
    
    # Si la bd está vacía, la suma da None, lo pasamos a 0
    totales_dict = {
        'cervezas': totales['cervezas'] or 0,
        'cubatas': totales['cubatas'] or 0,
        'chupitos': totales['chupitos'] or 0
    }
    
    conn.close()
    return render_template_string(HTML, amigos=amigos, totales=totales_dict)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre'].strip()
    hora_actual = datetime.now().strftime("%H:%M")
    
    if nombre:
        conn = get_db()
        try:
            conn.execute('INSERT INTO amigos (nombre, hora) VALUES (?, ?)', (nombre, hora_actual))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Si el nombre ya existe, lo ignoramos para que no pete
        finally:
            conn.close()
            
    return redirect(url_for('index'))

@app.route('/sumar', methods=['POST'])
def sumar():
    amigo_id = request.form['id']
    bebida = request.form['bebida'] # 'cervezas', 'cubatas' o 'chupitos'
    hora_actual = datetime.now().strftime("%H:%M")
    
    # Por seguridad en bases de datos, comprobamos que el nombre de la columna es correcto
    if bebida in ['cervezas', 'cubatas', 'chupitos']:
        conn = get_db()
        # Incrementamos la bebida correspondiente y actualizamos la hora
        sql = f'UPDATE amigos SET {bebida} = {bebida} + 1, hora = ? WHERE id = ?'
        conn.execute(sql, (hora_actual,
