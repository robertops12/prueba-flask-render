from flask import Flask

# Inicializamos la aplicación
app = Flask(__name__)

# Creamos la ruta principal (la página de inicio)
@app.route('/')
def inicio():
    return "¡Hola! Mi aplicación de Python está funcionando perfectamente en Render 🚀"

# Esto es necesario para que funcione localmente si quieres probarlo
if __name__ == '__main__':
    app.run(debug=True)