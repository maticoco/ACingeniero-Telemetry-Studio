# Telemetry Studio / ACingeniero

Bienvenido a **Telemetry Studio / ACingeniero**, la plataforma de ingeniería de carreras definitiva para Assetto Corsa. Esta herramienta te permite grabar, visualizar y comparar datos de telemetría en tiempo real mediante un avanzado panel de control interactivo, un simulador de ingeniero de pista (AI Coach) y métricas de desempeño de vehículos y neumáticos.

## 🚀 Instalación y Despliegue

1. **Requisitos Previos:**
   Asegúrate de tener instalado Python 3.9 o superior.

2. **Instalar Dependencias:**
   Ejecuta el siguiente comando en tu terminal para instalar todas las librerías necesarias:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la Aplicación:**
   Inicia la interfaz gráfica mediante Streamlit:
   ```bash
   streamlit run telemetry_app.py
   ```

## 🛠️ Guía de Uso

La aplicación está dividida en varias pestañas modulares para aislar tu flujo de trabajo:

- **🔴 Captura en Vivo:** Lanza el grabador de memoria en segundo plano ("Headless"). Selecciona o escanea tu directorio de límites y la aplicación guardará automáticamente tus vueltas extrayendo nombre de pista y coche directamente desde Assetto Corsa.
- **📊 Análisis (Driver Analysis):** Gráficos de telemetría pura (Acelerador, Freno, Velocidad, RPM, Marcha) a lo largo de la distancia de la pista. Te permite visualizar tu progresión a nivel macro.
- **🗺️ Dominio de Pista (Track Map):** Renderizado espacial (2D/3D) del asfalto del circuito (extraído de los ficheros `.ai` originales) con tus trazadas superpuestas mediante gradientes (Heatmap de frenada y aceleración). 
- **🏎️ Dinámica del Coche (Car Dynamics):** Evaluación de balance aerodinámico y fuerzas G (Círculo de Tracción o G-Circle) para que puedas auditar el comportamiento mecánico de la suspensión y detectar subviraje/sobreviraje.
- **🛞 Neumáticos y Frenos:** Diagnóstico de las tres franjas de temperatura del neumático (I/M/O) y temperatura de los discos de freno.
- **🤖 Asistente de Pilotaje IA (AI Coach):** Genera un "Debrief" automático utilizando matemáticas espaciales (cKDTree). Identifica métricamente el punto exacto en la pista donde has perdido velocidad (Delta V) respecto a tu vuelta base y te da un diagnóstico conciso.

## 🏁 Grabación de una Sesión

1. Abre Assetto Corsa y sal a la pista (necesitas estar en el coche para que la memoria compartida comience a emitir a 60Hz).
2. Ve a la pestaña **🔴 Captura en Vivo** en Telemetry Studio.
3. Presiona **Iniciar Grabación**.
4. ¡Conduce! Todas tus vueltas quedarán grabadas en tiempo real. 
5. Cuando termines, presiona **Detener**, despliega la barra lateral izquierda (Sidebar) y carga las vueltas capturadas para analizar tu rendimiento.
