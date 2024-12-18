from flask import Flask, render_template, request, redirect, url_for, Response, session
import redis
import functools

app = Flask(__name__)
app.secret_key = 'secret_key_rvo'

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_auth(username, password):
            return redirect(url_for('index'))
        else:
            return "Credenciales incorrectas", 401
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    try:
        return redirect(url_for('login'))  # Redirige al index
    except Exception as e:
        return f"Error en logout: {str(e)}", 500


@app.route('/')
@requires_auth
def index():
    key = 'selected_pins'
    selected_pins = r.lrange(key, 0, -1)  # Obtener lista de pines seleccionados
    selected_pins = [int(pin) for pin in selected_pins]  # Convertir a enteros
    server = r.get('server')
    # server = _server.decode('utf-8') if _server else 'localhost'

    return render_template('index.html', selected_pins=selected_pins, server=server)


@app.route('/update_pines', methods=['POST'])
@requires_auth
def update_pines():
    # La clave es fija: "pines"
    key = 'pines'
    key2 = 'selected_pins'
    # Obtener los valores enviados desde el formulario
    values = request.form['value']
    # Convertir la cadena en una lista de números (suponiendo que los valores están separados por comas)
    try:
        value_list = [int(x.strip()) for x in values.split(',')]
    except ValueError:
        return "Todos los valores deben ser números separados por comas.", 400

    # Validar la cantidad de valores
    if not (1 <= len(value_list) <= 8):
        return "Debes ingresar entre 1 y 8 valores.", 400
    
    # Actualizar la lista en Redis
    r.delete(key)  # Borra la lista anterior
    r.set(key, "{}".format(values))  # Agrega los nuevos valores

    # Guardar los valores en Redis
    r.delete(key2)  # Eliminar la lista anterior
    r.rpush(key2, *value_list)  # Guardar los nuevos valores

    return redirect(url_for('index'))


@app.route('/update_server', methods=['POST'])
@requires_auth
def update_server():
    key = 'server'
    server = request.form['server']
    r.set(key, "{}".format(server))

    return redirect(url_for('index'))


@app.route('/update_details')
@requires_auth
def update_details_form():
    key = 'selected_pins'
    selected_pins = r.lrange(key, 0, -1)  # Obtener los valores de la lista
    selected_pins = [int(pin) for pin in selected_pins]  # Convertir a enteros

    return render_template('update_details.html', selected_pins=selected_pins)


@app.route('/update_details', methods=['GET', 'POST'])
@requires_auth
def update_details():
    try:
        key = 'selected_pins'
        selected_pins = r.lrange(key, 0, -1)
        selected_pins = [int(pin) for pin in selected_pins]

        if request.method == 'POST':
            # Leer los datos enviados desde el formulario
            pin = int(request.form['pin'])
            device = request.form['device']
            habilitacion_zsf = request.form.get('habilitacion_zsf', '0')
            tiempo_zsf = int(request.form['tiempo_zsf'])
            habilitacion_osf = request.form.get('habilitacion_osf', '0')
            tiempo_osf = int(request.form['tiempo_osf'])

            # Guardar los datos en Redis con las claves especificadas
            r.set(f'devid_{pin}', device)
            r.set(f'zsf_{pin}', habilitacion_zsf)
            r.set(f'tl_zs_{pin}', tiempo_zsf)
            r.set(f'osf_{pin}', habilitacion_osf)
            r.set(f'tl_os_{pin}', tiempo_osf)

            # Pasar los valores a la plantilla
            return render_template('update_details.html', 
                                selected_pins=selected_pins, 
                                selected_pin=pin, 
                                device=device,
                                habilitacion_zsf=habilitacion_zsf, 
                                tiempo_zsf=tiempo_zsf,
                                habilitacion_osf=habilitacion_osf, 
                                tiempo_osf=tiempo_osf)

        # Para GET: Mostrar los valores por defecto si no se ha enviado el formulario
        return render_template('update_details.html', selected_pins=selected_pins)
    except Exception as e:
        return f"Ocurrió un error: {e}", 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
