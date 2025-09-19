# -*- coding: utf-8 -*-
from flask import Flask, request, render_template_string, Response, send_file
from redis import Redis, RedisError
import os
import socket
import tensorflow as tf
import json
import numpy as np

# Connect to Redis
REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
print("REDIS_HOST: " + REDIS_HOST)
redis = Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)
app = Flask(__name__)

ARCHIVO_ANOMALIAS = "resultados.txt"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Redis App</title>
</head>
<body>
    <h1><b>Mediciones de Juan Miguel Sarria Orozco</b></h1>
    <h2>Servidor: {{ hostname }}</h2>
    <form action="/detectar" method="get" style="margin-bottom: 10px;">
        <input type="text" name="dato" placeholder="Introduce un número" required>
        <button type="submit">Insertar</button>
    </form>
    <form action="/limpiar" method="post">
        <button type="submit">Limpiar</button>
    </form>
    <a href="/ver_anomalias">Ver datos de anomalías</a>
    <h2>Lista de mediciones guardadas:</h2>
    {% if numeros %}
        <ul>
            {% for numero, index in numeros %}
                <li>Medición {{ index }}: {{ numero }}</li>
            {% endfor %}
        </ul>
    {% else %}
        <p><b>No hay ninguna medición</b></p>
    {% endif %}
    
</body>
</html>
"""

# Función para renderizar la lista desde Redis
def obtener_lista():
    try:
        # Obtenemos las mediciones en un rango amplio
        mediciones = redis.execute_command('TS.RANGE', 'mediciones', '-', '+')
        numeros = [(f"Timestamp: {int(m[0])}, Valor: {float(m[1])}", idx + 1) for idx, m in enumerate(mediciones)]
        return numeros
    except RedisError as e:
        return [("Error al conectar con Redis: " + str(e), 0)]

@app.route("/", methods=["GET", "POST"])
@app.route("/listar", methods=["GET", "POST"])
def listar():
    numeros = obtener_lista()
    hostname = socket.gethostname()
    return render_template_string(HTML_TEMPLATE, numeros=numeros, hostname=hostname)

@app.route("/nuevo", methods=["GET"])
def nuevo():
    dato = request.args.get("dato")
    if not dato:
        return "Por favor, introduce un dato válido", 400

    try:
        float(dato)  # Validar que sea un número
        redis.execute_command('TS.ADD', 'mediciones', '*', dato)
        return "<script>window.location='/';</script>"
    except ValueError:
        return "Solo se permiten números (enteros o decimales). Intenta nuevamente.", 400
    except RedisError as e:
        return f"Error al conectar con Redis: {str(e)}", 500

@app.route("/limpiar", methods=["POST"])
def limpiar():
    try:
        # Eliminar las mediciones en Redis
        redis.execute_command('DEL', 'mediciones')
        # Limpiar el archivo de texto
        with open("resultados.txt", "w") as file:
            file.write("")  # Sobrescribe el archivo con contenido vacío
    except RedisError:
        return "Error al conectar con Redis", 500
    except IOError:
        return "Error al limpiar el archivo de resultados", 500
    return "<script>window.location='/';</script>"


@app.route("/detectar", methods=["GET"])
def detectar():
    # Cargar el dato
    dato = request.args.get("dato")
    if not dato:
        return "Por favor, introduce un dato válido", 400

    try:
        dato_float = float(dato)

        # Cargar el modelo
        modelo = tf.keras.models.load_model('modelo.keras')

        # Cargar el umbral
        with open("threshold.txt", "r") as file:
            threshold = float(file.read().strip())
        
        # Agregar el nuevo dato a Redis
        redis.execute_command('TS.ADD', 'mediciones', '*', dato)

        # Obtener las mediciones
        mediciones = redis.execute_command('TS.RANGE', 'mediciones', '-', '+')

        if len(mediciones) <= 3:
            # Si hay menos de 3 mediciones, registrar siempre como no anomalía
            pos = len(mediciones);
            resultado = {
             f"medicion {pos}": {
             "time": int(mediciones[pos-1][0]),  # timestamp
                "valor": float(mediciones[pos-1][1]),  # valor de la medición
               "anomalia": "no"
            }
         }
        else:
            # Tomar las últimas 3 mediciones
            ventana = mediciones[-4:-1]
            valores_ventana = [float(m[1]) for m in ventana]
            valores_ventana = np.array(valores_ventana).reshape((1, 3, 1))

            #Realizar predicción con el modelo
            prediccion = modelo.predict(valores_ventana)[0][0]

            # Calcular la diferencia y verificar anomalía
            error = abs(prediccion - dato_float)
            anomalia = "si" if error > threshold else "no"

            # Preparar el resultado
            pos = len(mediciones);
            resultado = {

              f"medicion {pos}": {  # El número de la medición será el tamaño de la lista
                "time": int(mediciones[pos-1][0]),  # timestamp de la última medición
                  "valor": float(mediciones[pos-1][1]),  # valor de la última medición
                  "prediccion": float(prediccion),
                  "anomalia": anomalia  # Anomalía calculada
                }
              }

        # Escribir el resultado en el archivo, añadiendo una línea
        with open("resultados.txt", "a") as file:
            file.write(json.dumps(resultado, ensure_ascii=False) + "\n")

        # Devolver el resultado como respuesta
        return "<script>window.location='/';</script>"

    except ValueError:
        return "Solo se permiten números válidos. Intenta nuevamente.", 400
    except FileNotFoundError as e:
        return f"No se encontró el archivo necesario: {str(e)}", 500
    except RedisError as e:
        return f"Error al conectar con Redis: {str(e)}", 500

@app.route("/ver_anomalias", methods=["GET"])
def ver_anomalias():
    if not os.path.exists(ARCHIVO_ANOMALIAS) or os.path.getsize(ARCHIVO_ANOMALIAS) == 0:
        return "El archivo de anomalías está vacío o no existe.", 404
    return send_file(ARCHIVO_ANOMALIAS, as_attachment=True)

if __name__ == "__main__":
    PORT = os.getenv('PORT', 80)
    print("PORT: " + str(PORT))
    app.run(host='0.0.0.0', port=PORT)