from flask import Flask, request, render_template_string

app = Flask(__name__)

# Esta lista guardará los datos de todos los amigos durante la fiesta
amigos = []

# Diseño de la aplicación (Modo noche / Fiesta)
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nivel de Fiesta de los Colegas 🍻</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2f; color: white; text-align: center; padding: 20px; }
        .container { background: #2a2a40; max-width: 500px; margin: auto; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); }
        input, select, button { width: 90%; margin: 10px 0; padding: 10px; border-radius: 5px; border: none; font-size: 16px; box-sizing: border-box; }
        input, select { background-color: #3e3e5c; color: white; }
        button { background-color: #ff4757; color: white; font-weight: bold; cursor: pointer; margin-top: 15px; }
        button:hover { background-color: #ff6b81; }
        .lista-amigos { margin-top: 30px; text-align: left; }
        .amigo-card { background: #3e3e5c; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #ccc; }
        /* Colores según el estado elegido */
        .estado-Sobrio { border-color: #2ed573; }
        .estado-Puntillo { border-color: #1e90ff; }
        .estado-Borracho { border-color: #ffa502; }
        .estado-Ebrio { border-color: #ff4757; }
        h3 { border-bottom: 1px solid #555; padding-bottom: 10px; }
    </style>
</head>
<body>

<div class="container">
    <h2>Muro de la Fiesta 🍻</h2>
    <p>Apunta lo que llevas y elige tu estado para ver quién aguanta más.</p>

    <form method="POST">
        <label>Tu Nombre:</label>
        <input type="text" name="nombre" required placeholder="Ej. Juan">

        <label>🍺 Cervezas:</label>
        <input type="number" name="cervezas" value="0" min="0">

        <label>🍹 Cubatas:</label>
        <input type="number" name="cubatas" value="0" min="0">

        <label>🥃 Chupitos:</label>
        <input type="number" name="chupitos" value="0" min="0">

        <label>¿Cómo te sientes ahora mismo?:</label>
        <select name="estado">
            <option value="Sobrio">Fresquísimo / Sobrio 💧</option>
            <option value="Puntillo">Con el puntillo alegre 🕺</option>
            <option value="Borracho">Borracho / Perdiendo los papeles 🥴</option>
            <option value="Ebrio">Ebrio Extremo / En la miseria 💀</option>
        </select>

        <button type="submit">¡Actualizar mi estado!</button>
    </form>

    <div class="lista-amigos">
        <h3>Niveles de la gente:</h3>
        {% if amigos|length == 0 %}
            <p style="text-align: center; color: #aaa;">Aún nadie ha apuntado nada. ¡Sé el primero!</p>
        {% else %}
            {% for amigo in amigos %}
            <div class="amigo-card estado-{{ amigo.estado }}">
                <strong style="font-size: 1.2em;">{{ amigo.nombre }}</strong> se siente <em>{{ amigo.estado }}</em><br>
                <span style="color: #bbb; font-size: 0.9em;">Ha bebido: {{ amigo.cervezas }} 🍺 | {{ amigo.cubatas }} 🍹 | {{ amigo.chupitos }} 🥃</span>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Recogemos lo que el usuario ha rellenado
        nombre = request.form['nombre']
        cervezas = int(request.form['cervezas'])
        cubatas = int(request.form['cubatas'])
        chupitos = int(request.form['chupitos'])
        estado = request.form['estado'] # Aquí recogen el estado que han elegido a mano

        # 2. Buscamos si el amigo ya existe en la lista para actualizarlo
        encontrado = False
        for amigo in amigos:
            if amigo['nombre'].lower() == nombre.lower():
                amigo['cervezas'] = cervezas
                amigo['cubatas'] = cubatas
                amigo['chupitos'] = chupitos
                amigo['estado'] = estado
                encontrado = True
                break
        
        # 3. Si es un amigo nuevo que no estaba en la lista, lo añadimos
        if not encontrado:
            amigos.append({
                'nombre': nombre,
                'cervezas': cervezas,
                'cubatas': cubatas,
                'chupitos': chupitos,
                'estado': estado
            })

    # Mostramos la página web pasándole la lista de amigos
    return render_template_string(HTML, amigos=amigos)

if __name__ == '__main__':
    app.run(debug=True)