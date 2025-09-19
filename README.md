# Coordinación de Nodos con Docker Swarm

Este repositorio contiene un proyecto que demuestra la coordinación de múltiples nodos utilizando Docker Swarm.

---

## Instrucciones para probar la coordinación de nodos

1. **Iniciar Docker Swarm**  
   Ejecuta el comando para iniciar Docker Swarm en tu máquina.
    - docker swarm init

2. **Ejecutar el stack**  
   Despliega el stack utilizando el archivo `docker-compose.yml` y asigna un nombre al stack.
    - docker stack deploy -c docker-compose.yml nombreStack

3. **Eliminar el stack**  
   Elimina el stack cuando ya no lo necesites.
    - docker stack rm nombreStack

4. **Cerrar Docker Swarm**  
   Sal de Docker Swarm para cerrar todos los servicios relacionados.
    - docker swarm leave

---

## Acceder a los servicios

Una vez que el stack esté corriendo, podemos acceder a los diferentes servicios desde el navegador:

- **Aplicación web:**  
  Accede a [http://localhost:4000](http://localhost:4000) para ver cómo se añaden los datos automáticamente y cada vez que actualizemos veras uno de los servidores distintos (5 replicas despegadas).

- **Grafana:**  
  Accede a [http://localhost:3000](http://localhost:3000) para ver cómo se actualizan cada 5 segundos las medias de los datos almacenados.  
  > La configuración de Redis en Grafana está explicada en el PDF `02_Guia Docker.pdf`.

- **Visualizer:**  
  Accede a [http://localhost:8080](http://localhost:8080) para visualizar la topología de los servicios y contenedores.

---

## Información adicional

En todos los PDFs incluidos en el repositorio encontrarás guías detalladas sobre cómo utilizar cada servicio y configuraciones adicionales.  
Esto permite comprender mejor el flujo de datos y cómo los servicios interactúan entre sí.
