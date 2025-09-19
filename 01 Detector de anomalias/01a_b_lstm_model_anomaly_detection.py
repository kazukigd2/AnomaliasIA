from numpy import array
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.layers import Input


# Cargar los datos (7267,1) (según el fichero cambiará el número de filas)
df = pd.read_csv("datos.csv",parse_dates=True)

# Creo mis 2 dataFrames con ambas columnas y se crean las ventanas temporales
columnaDatos = df['value']
columnaFechas= df['timestamp']
nDatosVentana = 3
ventana = np.lib.stride_tricks.sliding_window_view(columnaDatos, window_shape=nDatosVentana)

# Dividir los datos en entrenamiento y prueba es lo habitual
X = array(ventana[:-1])  # Todas las ventanas menos la última. Hay que convertir a array numpy
y = array(columnaDatos[nDatosVentana:])  # Lo que predices (el siguiente valor después de cada ventana)

porcentaje_entrenamiento = 0.7
nEntrenamiento = int(len(X) * porcentaje_entrenamiento)

X_train, X_test = X[:nEntrenamiento], X[nEntrenamiento:]
y_train, y_test = y[:nEntrenamiento], y[nEntrenamiento:]

# Redimensionar los datos para la RNN
# LSTM espera 3 dimensiones: número muestras, pasos temporales, número features
n_features = 1
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], n_features))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], n_features))

# Crear la RNN
model = Sequential()
model.add(Input(shape=(nDatosVentana, n_features)))
model.add(LSTM(50, activation='relu'))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# Entrenar la RNN
model.fit(X_train, y_train, epochs=30, batch_size=32, validation_data=(X_test, y_test))

# Guardar el entrenamiento de la RNN
model.save('modelo.keras')

# Hacer predicciones sobre todo el conjunto
y_pred = model.predict(X)

#Aplano los datos de las predicciones y los transformo en un array de numpy para trabajar mejor con ellos
y_pred_trimmed = y_pred.flatten()
y_predArray = array(y_pred_trimmed)

# Calcular el error absoluto para cada predicción
errors = abs(y.flatten() - y_predArray.flatten())

# Calcular la media y la desviación estándar de los errores
mae = np.mean(errors)
std_error = np.std(errors)

# Establecer un umbral para las anomalías
threshold = mae + 2 * std_error  # Por ejemplo, 2 desviaciones estándar

# Guardar el umbral en un archivo .txt
with open("threshold.txt", "w") as file:
    file.write(str(threshold))

#Imprimo por pantalla los valores
print(f"Error Absoluto Medio (MAE): {mae}")
print(f"Desviacion estandar: {std_error}")
print(f"Umbral: {threshold}")

# Paso a array de numpy el dataTable de fechas para manipularlo mejor y creo un array de anomalias de booleanos
columnaFechas = array(columnaFechas[nDatosVentana:])
anomalies = []

#Creo mi array con las anomalias e imprimo por pantalla las anomalias y sus diferencias
for index in range(len(y_predArray)):
    if errors[index] > threshold:  # Verificamos si es una anomalia
        expected = y_predArray[index]  # Valor esperado
        received = y[index]     # Valor recibido
        difference = abs(received - expected)  # Diferencia
        print(f"Fecha: {columnaFechas[index]}, Esperado: {expected}, Recibido: {received}, Diferencia: {difference}")
        plt.text(columnaFechas[index], y[index], f"{errors[index]:.2f}", color='red', fontsize=8, ha='right')
        anomalies.append(True)
    else:
       anomalies.append(False)

anomalies = np.array(anomalies)

#Resumen de las anomalias
print("El número de anomalías es " + str(np.sum(anomalies)) + " sobre " + str(df.shape[0]))

#Todas las funciones de matplotlab para mostrar la grafica de la manera que quiero hacera
#Muestro una linea azul con los valores reales, otras linea amarilla con las predicciones, y puntos rojos con las anomalias en los valores reales
#Y puntos verdes con las anomalias en las predicciones y el valor de la diferencia en los puntos rojos, ademas
#Divido las fechas cada 3 dias para no colapsar la grafica
plt.plot(columnaFechas, y, color='blue',label='Datos originales')
plt.plot(columnaFechas, y_predArray, color='yellow', linestyle='--', label='Predicciones')   # Añadir y_pred en color amarillo
plt.scatter(x=columnaFechas, y=y, c='red', alpha=anomalies.astype(int),s=50, label='Anomalias')
plt.scatter(x=columnaFechas, y=y_predArray, c='green', alpha=anomalies.astype(int),s=50)
plt.xlabel("Fecha")
plt.ylabel("Valor")
plt.title("Detección de Anomalías")

columnaFechas = pd.to_datetime(columnaFechas)
tick_positions = np.arange(0, len(columnaFechas), 72)  # Crear intervalos cada 72 puntos de datos
tick_labels = [date.strftime("%Y-%m-%d %H") for date in columnaFechas[tick_positions]]  # Formatear las fechas

plt.xticks(tick_positions, tick_labels, rotation=70, fontsize=8)

plt.legend()
plt.show()
