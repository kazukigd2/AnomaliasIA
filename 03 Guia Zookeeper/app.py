# -*- coding: utf-8 -*-
from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import os
import threading
import time
import random
import requests
import signal


#VARIABLES
#=========
dato = 0
url = 'http://web:80/detectar'
#url = 'http://127.0.0.1/detectar'
id = os.environ.get('INSTANCE_ID', str(random.randint(10000000, 99999999)))
ZOOKEEPER_HOST = os.getenv("ZOOKEEPER_HOST", "localhost:2181") 
zk =  KazooClient(hosts=ZOOKEEPER_HOST, timeout=30)
#Comienza el cliente zookeper
zk.start()


#FUNCIONES
#=========

#Funcion que le envias una url y un valor y envia el dato a esa url
def enviarDato(valor):
    params = {'dato': valor}
    try:
        response = requests.get(url, params=params) # Hacemos la petición GET con el parámetro y guardamos la respuesta en una variable
    except:
        print("El dato no se envio al servidor dado que hubo un error al conectar con el mismo")

# Función que se ejecuta cuando se recibe la señal de interrupción y se cierra
def interrupt_handler(signal, frame):
    exit(0)

#Funcion que crea un nodo con un valor
def crearNodo(valor):
    try:
        zk.ensure_path("/my/favorite")
        zk.create(f"/my/favorite/{id}", str(valor).encode("utf-8"), ephemeral=True)
        print("Nodo creado")
    except:
        print('Error al crear nodo.')

#Funcion que devuelve si existe o no el nodo
def existeNodo():
    return zk.exists("/my/favorite") is not None

#Funcion que devuelve el nodo
def getNodo():
    try:
        (data, _) = zk.get(f"/my/favorite/{id}")
        return data.decode("utf-8")
    except Exception as e:
        print(f"Error al obtener el nodo: {e}")
        return None

#Funcion que devuelve la lista de hijos (que no el valor)
def getListaHijos():
    try:
        children = zk.get_children("/my/favorite")
        return children
    except Exception as e:
        print(f"Error al obtener los hijos: {e}")
        return []

#Funcion para devolver el valor de los hijos
def getValoresHijos():
    # Obtener todos los hijos de /my/favorite
    if existeNodo():
        children = zk.get_children("/my/favorite")
        
        # Lista para almacenar los valores de los hijos
        valores = []

        # Obtener el valor de cada hijo
        for hijo in children:
            try:
                data, _ = zk.get(f"/my/favorite/{hijo}")
                valores.append(float(data))
            except Exception as e:
                print(f"Error al obtener el valor del hijo {hijo}: {e}")
        return valores
    else:
        print("El nodo /my/favorite no existe.")
        return []


#Funcion que devuelve el dato de un nodo
def getDatosNodo(id):
    try:
        (data, _) = zk.get(f"/my/favorite/{id}")
        return float(data)
    except Exception as e:
        print(f"Error al obtener los datos del nodo {id}: {e}")
        return None

#Funcion que setea el valor de un nodo
def setDatosNodo(valor):
    try:
        if zk.exists(f"/my/favorite/{id}"):
            zk.set(f"/my/favorite/{id}", str(valor).encode("utf-8"))
        else:
            zk.create(f"/my/favorite/{id}", str(valor).encode("utf-8"), ephemeral=True)
    except Exception as e:
        print(f"Error al setear el valor del nodo: {e}")


# Funcion que ejecuta el lider para hacer la media de todos los hijos y enviarla al servidor
def leader_func():
    print("Soy el nuevo lider")
    while True:
        valores = getValoresHijos()

        if valores:  # Evitar dividir por cero
            print(valores)
            media = sum(valores) / len(valores)
            print(f"La media es: {media}")
            enviarDato(media)
        else:
            print("No hay valores disponibles para calcular la media.")

        # Enviar la media usando requests
        time.sleep(5)


#Funcion que decide el lider
def election_func():
    election.run(leader_func)


#PROGRAMA
#========


# Registrar la función como el manejador de la señal de interrupción
signal.signal(signal.SIGINT, interrupt_handler)

# Crear una elección entre las aplicaciones y elegir un líder
election = Election(zk, "/election",id)

# Crear un hilo para ejecutar la función election_func
election_thread = threading.Thread(target=election_func, daemon=True)

# Iniciar el hilo
election_thread.start()
# Enviar periódicamente un valor a una subruta de /mediciones con el identificador de la aplicación
while True:
    # Generar una nueva medición aleatoria
    dato = random.randint(75, 85)
    
    # Crea un nodo si no existe o setea un nuevo valor del nodo
    if existeNodo():
        setDatosNodo(dato)
    else:
        crearNodo(dato)
    time.sleep(5)
 