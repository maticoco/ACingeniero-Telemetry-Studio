# Documentación Técnica: Arquitectura Telemetry Studio (v2.0)

Este documento detalla los principios de diseño y las decisiones arquitectónicas que sustentan la plataforma de análisis de telemetría de Assetto Corsa.

## 🏗️ 1. Arquitectura General y Desacoplamiento (Headless)

El sistema opera bajo un paradigma de procesos separados (desacoplamiento total):
- **Frontend / Orquestador (Síncrono):** La interfaz visual (`telemetry_app.py`) corre sobre el bucle de eventos de Streamlit. Renderiza los mapas y gráficas sin sufrir caídas de frames causadas por I/O pesados en disco.
- **Backend / Grabador (Asíncrono & Headless):** El motor de captura (`record_session.py` y `telemetry_standalone\`) se lanza como un subproceso en segundo plano usando `subprocess.Popen`. Se conecta directamente a la memoria física compartida (Shared Memory a través de `mmap` y `ctypes`) y graba a 60Hz. Toda la configuración de rutas y parámetros se inyecta silenciosamente mediante variables de entorno (`os.environ`).

## 💾 2. Modelo de Datos Centralizado (`loaded_laps`)

La interfaz multi-vuelta no depende de comparativas binarias fijas (una contra otra). Emplea una estructura en memoria orientada a objetos (Diccionarios en Python) gestionada en el estado de Streamlit (`st.session_state`):
- `loaded_laps` es una lista donde cada elemento es un objeto "Vuelta" (Lap Object).
- Cada Lap Object contiene: su **DataFrame** (Pandas), un identificador único, sus **metadatos** (tiempo, coche, pista) y un **Theme visual** asignado desde el Gestor Dinámico (colores para el coche, freno, acelerador y trazo).
- Toda la UI itera sobre `loaded_laps` escalando desde 1 coche hasta el infinito sin romper el diseño.

## 📐 3. Motor KDTree Espacial (AI Coach)

Para evaluar dónde un piloto gana o pierde tiempo en comparación con otra vuelta, el sistema **no confía en el tiempo o la distancia recorrida linealmente**, ya que esto genera desincronización por trazadas diferentes. Se usa **Matemática Espacial**:
- Se inicializa un árbol espacial multidimensional `scipy.spatial.cKDTree` inyectando todas las coordenadas espaciales (`pos_x`, `pos_z`) de la "Vuelta Base" (la referencia).
- Al comparar, el algoritmo interpola cada coordenada del coche evaluado consultando el árbol (`tree.query()`) para encontrar su equivalente físico exacto en la vuelta de referencia.
- Esto permite calcular el *Delta V* (Velocidad Comparado vs Velocidad Base en el mismo milímetro del asfalto) y el error cruzado (Producto vectorial) para medir desviaciones de vértice (Apex Deltas) con precisión de ingeniero.

## 🗺️ 4. Motor Híbrido de Mapas y Escáner Dinámico (Track Limits)

El Track Map no depende de imágenes estáticas. Es un entorno vivo en Plotly:
- **Escáner Dinámico:** Un módulo interno abre, lee y decodifica el archivo binario `fast_lane.ai` directo del juego usando estructuras C (`struct 4fi`). A través de matemáticas de vectores normales extrae los límites izquierdo y derecho de la pista calculando distancias de ~8.5 metros por lado del centro de la IA y los guarda en un archivo `_track_limits.csv`.
- **Renderizado Híbrido:** Si cargas una pista desconocida que carece de su `.csv` vectorizado, el `try/except FileNotFoundError` atrapa la excepción y realiza un **Fallback silencioso**. El mapa se negará a dibujar los límites grises, dejando la pantalla en negro espacial pero renderizando encima la telemetría viva para evitar el colapso de la aplicación.
