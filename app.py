from flask import Flask, render_template, request, redirect, url_for, Response
import redis
import functools

app = Flask(__name__)

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Configurar las credenciales de autenticación
USERNAME = 'admin'
PASSWORD = 'password'

def check_auth(username, password):
    """Función que verifica si las credenciales son correctas."""
    return username == USERNAME and password == PASSWORD

def authenticate():
    """Envía una respuesta 401 para solicitar autenticación."""
    return Response(
        'Necesitas autenticarte para acceder a esta página', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """Decorador para proteger rutas con autenticación."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

@app.route('/update', methods=['POST'])
@requires_auth
def update():
    key = request.form['key']
    value = request.form['value']
    r.set(key, value)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
