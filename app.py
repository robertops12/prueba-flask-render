from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

# Lista global de la fiesta
amigos = []

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Party Tracker Pro 🍻</title>
    <style>
        :root {
            --bg-color: #12121c;
            --card-bg: #1e1e2f;
            --input-bg: #2a2a40;
            --text-main: #ffffff;
            --text-muted: #a0a0b5;
            --accent: #ff4757;
            --success: #2ed573;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        
        /* Dashboard Stats */
        .dashboard { display: flex; justify-content: space-between; background: var(--card-bg); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .stat-box { text-align: center; width: 30%; }
        .stat-box span { display: block; font-size: 24px; font-weight: bold; color: var(--text-main); }
        .stat-box small { color: var(--text-muted); font-size: 12px; text-transform: uppercase; }

        /* Formularios y Tarjetas */
        .card { background: var(--card-bg); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; }
        input, select, button { width: 100%; margin: 8px 0 16px; padding: 12px; border-radius: 8px; border: none; font-size: 16px; box-sizing: border-box; }
        input, select { background-color: var(--input-bg); color: var(--text-main); }
        input:focus, select:focus { outline: 2px solid var(--accent); }
        
        button { background-color: var(--accent); color: white; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { filter: brightness(1.1); }
        .btn-reset { background-color: transparent; border: 1px solid var(--accent); color: var(--accent); margin-top: 0; }
        
        /* Lista de amigos */
        .amigo-card { background: var(--input-bg); padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 5px solid #ccc; display: flex; flex-direction: column; position: relative; }
        .amigo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .amigo-nombre { font-size: 1.1em; font-weight: bold; }
        .badge-hora { background: #000; color: #fff; padding: 3px 8px; border-radius: 12px; font-size: 11px; opacity: 0.8; }
        
        .estado-Sobrio { border-color: var(--success); }
        .estado-Puntillo { border-color: #1e90ff; }
        .estado-Borracho { border-color: #ffa502; }
        .estado-Ebrio { border-color: var(--accent); }
        
        .amigo-consumo { color: var(--text-muted); font-size: 0.9em; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; margin-top: 8px; }
    </style>
</head>
<body>

<div class="container">
    <h2 style="text-align: center; margin-bottom: 5px;">Party Tracker Pro 🍻</h2>
    <p style="text-align: center; color: var(--text-muted); margin-top: 0; margin-bottom: 20px;">Registro oficial de la noche</p>

    <div class="dashboard">
        <div class="stat-box"><span>{{ total_cervezas }}</span><small>Cervezas</small></div>
        <div class="stat-box"><span>{{ total_cubatas }}</span><small>Cubatas</small></div>
        <div class="stat-box"><span>{{ total_chupitos }}</span><small>Chupitos</small></div>
    </div>

    <div class="card">
        <form method="POST">
            <input type="hidden" name="accion" value="actualizar">
            
            <label>Tu Nombre:</label>
            <input type="text" name="nombre" required placeholder="Ej. Juan">

            <div style="display: flex; gap: 10px;">
                <div style="width: 33%;">
                    <label>🍺 Cerv.</label>
                    <input type="number" name="cervezas" value="0" min="0">
                </div>
                <div style="width: 33%;">
                    <label>🍹 Cub.</label>
                    <input type="number" name="cubatas" value="0" min="0">
                </div>
                <div style="width: 33%;">
                    <label>🥃 Chup.</label>
                    <input type="number" name="chupitos" value="0" min="0">
                </div>
            </div>

            <label>¿Cómo te sientes ahora mismo?:</label>
            <select name="estado">
                <option value="Sobrio">Fresquísimo / Sobrio 💧</option>
                <option value="Puntillo">Con el puntillo alegre 🕺</option>
                <option value="Borracho">Borracho / Perdiendo los papeles 🥴</option>
                <option value="Ebrio">Ebrio Extremo / En la miseria 💀</option>
            </select>

            <button type="submit">Actualizar mi estado</button>
        </form>
    </div>

    <h3 style="border-bottom: 1px solid var(--input-bg); padding-bottom: 10px;">Timeline de la fiesta:</h3>
    {% if amigos|length == 0 %}
        <p style="text-align: center; color: var(--text-muted);">El muro está vacío. ¡Que empiece la fiesta!</p>
    {% else %}
        {% for amigo in amigos %}
        <div class="amigo-card estado-{{ amigo.estado }}">
            <div class="amigo-header">
                <span class="amigo-nombre">{{ amigo.nombre }} <span style="font-weight: normal; font-size: 0.9em;">está <em>{{ amigo.estado }}</em></span></span>
                <span class="badge-hora">{{ amigo.hora }}</span>
            </div>
            <div class="amigo-consumo">
                Lleva: {{ amigo.cervezas }} 🍺 • {{ amigo.cubatas }} 🍹 • {{ amigo.chupitos }} 🥃
            </div>
        </div>
        {% endfor %}
    {% endif %}

    <div class="card" style="margin-top: 40px; border: 1px dashed var(--text-muted); background: transparent;">
        <h4 style="margin-top: 0;">Zona Admin 🧹</h4>
        <form method="POST" style="margin: 0;">
            <input type="hidden" name="accion" value="resetear">
            <input type="password" name="password" placeholder="Contraseña de reseteo..." required>
            <button type="submit" class="btn-reset">Borrar todos los datos</button>
        </form>
        {% if error %}
            <p style="color: var(--accent); font-size: 14px; margin-top: 10px;">{{ error }}</p>
        {% endif %}
    </div>
</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    mensaje_error = ""

    if request.method == 'POST':
        accion = request.form.get('accion')

        if accion == 'resetear':
            password = request.form.get('password')
            if password == '1234':
                amigos.clear()
            else:
                mensaje_error = "Contraseña incorrecta ❌"

        elif accion == 'actualizar':
            nombre = request.form.get('nombre').strip()
            cervezas = int(request.form.get('cervezas', 0))
            cubatas = int(request.form.get('cubatas', 0))
            chupitos = int(request.form.get('chupitos', 0))
            estado = request.form.get('estado')
            
            # Hora actual (formato HH:MM)
            hora_actual = datetime.now().strftime("%H:%M")

            # Buscar si el amigo ya existe
            amigo_existente = None
            for amigo in amigos:
                if amigo['nombre'].lower() == nombre.lower():
                    amigo_existente = amigo
                    break
            
            if amigo_existente:
                # Actualizamos sus datos
                amigo_existente['cervezas'] = cervezas
                amigo_existente['cubatas'] = cubatas
                amigo_existente['chupitos'] = chupitos
                amigo_existente['estado'] = estado
                amigo_existente['hora'] = hora_actual
                
                # Lo movemos al principio de la lista (Timeline)
                amigos.remove(amigo_existente)
                amigos.insert(0, amigo_existente)
            else:
                # Si es nuevo, lo añadimos al principio de la lista
                nuevo_amigo = {
                    'nombre': nombre,
                    'cervezas': cervezas,
                    'cubatas': cubatas,
                    'chupitos': chupitos,
                    'estado': estado,
                    'hora': hora_actual
                }
                amigos.insert(0, nuevo_amigo)

    # Calcular totales para el Dashboard
    total_cervezas = sum(a['cervezas'] for a in amigos)
    total_cubatas = sum(a['cubatas'] for a in amigos)
    total_chupitos = sum(a['chupitos'] for a in amigos)

    return render_template_string(HTML, 
                                  amigos=amigos, 
                                  error=mensaje_error,
                                  total_cervezas=total_cervezas,
                                  total_cubatas=total_cubatas,
                                  total_chupitos=total_chupitos)

if __name__ == '__main__':
    app.run(debug=True)
