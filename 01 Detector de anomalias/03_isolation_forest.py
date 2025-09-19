import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

# Cargar los datos
df = pd.read_csv("datos.csv", parse_dates=True)
columnaDatos = df['value']
columnaFechas = df['timestamp']


# Convertir a array y reshape para Isolation Forest
X = columnaDatos.values.reshape(-1, 1)


# Configurar y entrenar Isolation Forest
clf = IsolationForest(contamination=0.01, random_state=0) 
clf.fit(X)

# Predecir anomalías
y_pred = clf.predict(X)

# Convertir a booleanos para anomalías (1: normal, -1: anómalo)
anomalies = y_pred == -1

# Imprimir anomalías y diferencias de valores
for index, is_anomaly in enumerate(anomalies):
    if is_anomaly:
        fecha = columnaFechas[index]
        valor = columnaDatos[index]
        print(f"Fecha: {fecha}, Valor: {valor} - Anomalía detectada")

# Resumen de las anomalías
print(f"El número de anomalías es {np.sum(anomalies)} sobre {df.shape[0]}")

# Visualización
columnaFechas = pd.to_datetime(columnaFechas)
plt.plot(columnaFechas, columnaDatos, color='blue', label='Datos originales')
plt.scatter(columnaFechas[anomalies], columnaDatos[anomalies], color='red', label='Anomalías')
plt.xlabel("Fecha")
plt.ylabel("Valor")
plt.title("Detección de Anomalías con Isolation Forest")
plt.legend()
plt.show()