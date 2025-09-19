from numpy import array
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import LSTM, Dense, RepeatVector, TimeDistributed, Input

# Cargar los datos
df = pd.read_csv("datos.csv", parse_dates=True)

# Crear los dataFrames con ambas columnas y ventanas temporales
columnaDatos = df['value']
columnaFechas = df['timestamp']
nDatosVentana = 5
ventana = np.lib.stride_tricks.sliding_window_view(columnaDatos, window_shape=nDatosVentana)

# Convertimos en array numpy
X = array(ventana)  

# Redimensionar los datos para el autoencoder
n_features = 1
X = X.reshape((X.shape[0], X.shape[1], n_features))

# Crear el autoencoder LSTM
model = Sequential()
model.add(Input(shape=(nDatosVentana, n_features)))
model.add(LSTM(100, activation='relu'))
model.add(RepeatVector(nDatosVentana))
model.add(LSTM(100, activation='relu', return_sequences=True))
model.add(TimeDistributed(Dense(1)))
model.compile(optimizer='adam', loss='mse')
model.summary()

# Entrenar el autoencoder
model.fit(X, X, epochs=100, batch_size=32)

# Hacer predicciones sobre el conjunto de datos
y_pred = model.predict(X)

# Calcular el error absoluto en cada predicción para identificar anomalías
errors = np.mean(abs(X - y_pred), axis=1)  # Error promedio por ventana

# Calcular el umbral basado en el error promedio y desviación estándar
mae = np.mean(errors)
std_error = np.std(errors)
threshold = 2 * mae + std_error

print(f"Error Absoluto Medio (MAE): {mae}")
print(f"Desviacion estandar: {std_error}")
print(f"Umbral: {threshold}")


# Convertir fechas a array de numpy
columnaFechas = array(columnaFechas[nDatosVentana - 1:])
anomalies = []

# Detectar e imprimir anomalías
for index in range(len(y_pred)):
    error = errors[index]
    if error > threshold:
        expected = y_pred[index, -1, 0]  # Último valor de la predicción para la ventana
        received = X[index, -1, 0]       # Último valor de los datos originales en la ventana
        difference = abs(received - expected)
        print(f"Fecha: {columnaFechas[index]}, Esperado: {expected}, Recibido: {received}, Diferencia: {difference}")
        anomalies.append(True)
    else:
        anomalies.append(False)

anomalies = np.array(anomalies)

# Resumen de las anomalías
print("El número de anomalías es " + str(np.sum(anomalies)) + " sobre " + str(df.shape[0]))

# Visualización de resultados
plt.plot(columnaFechas, columnaDatos[nDatosVentana - 1:], color='blue', label='Datos originales')
plt.plot(columnaFechas, y_pred[:, -1, 0], color='yellow', linestyle='--', label='Predicciones')  # Predicción en amarillo
plt.scatter(columnaFechas[anomalies], columnaDatos[nDatosVentana - 1:][anomalies], color='red', label='Anomalías')
plt.xlabel("Fecha")
plt.ylabel("Valor")
plt.title("Detección de Anomalías")

# Configurar ticks en el eje X cada 3 días para claridad
columnaFechas = pd.to_datetime(columnaFechas)
tick_positions = np.arange(0, len(columnaFechas), 72)
tick_labels = [date.strftime("%Y-%m-%d %H") for date in columnaFechas[tick_positions]]

plt.xticks(tick_positions, tick_labels, rotation=70, fontsize=8)
plt.legend()
plt.show()