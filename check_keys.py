import redis

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Ejemplo para leer un valor de Redis
key = 'dev1'
value = r.get(key)
print(f"Valor para '{key}': {value}")
