import csv
import os
import time
from datetime import datetime
import threading
import queue

class TelemetryRecorder:
    """
    Graba los datos de telemetría en tiempo real a un archivo CSV.
    Utiliza una cola (Queue) y un hilo (Thread) en segundo plano para 
    evitar bloquear el flujo principal (60Hz) durante la escritura en disco.
    """
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = os.environ.get('AC_SAVE_DIR', 'data/sessions')
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generar nombre de archivo único por sesión
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.output_dir, f"session_{timestamp}.csv")
        
        self.queue = queue.Queue()
        self.is_recording = False
        self.thread = None
        self.headers_written = False

    def start(self):
        self.is_recording = True
        self.thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.thread.start()
        print(f"[*] Grabación de telemetría iniciada: {self.filename}")

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join()
        print(f"[*] Grabación de telemetría finalizada. Guardado en: {self.filename}")

    def record(self, telemetry_data: dict):
        """Añade un paquete de telemetría a la cola para ser grabado."""
        if self.is_recording:
            # Agregamos timestamp local a la data para análisis temporal
            data_copy = telemetry_data.copy()
            data_copy["timestamp_local"] = time.time()
            self.queue.put(data_copy)

    def _writer_loop(self):
        """Bucle en segundo plano que consume la cola y escribe en el CSV."""
        with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
            writer = None
            
            # Seguir iterando mientras estemos grabando o haya elementos pendientes en la cola
            while self.is_recording or not self.queue.empty():
                try:
                    # Timeout para que evalúe periódicamente la condición del while
                    data = self.queue.get(timeout=0.5)
                    
                    # Escribir cabeceras de forma dinámica basándonos en el primer paquete
                    if not self.headers_written:
                        writer = csv.DictWriter(f, fieldnames=data.keys())
                        writer.writeheader()
                        self.headers_written = True
                        
                    writer.writerow(data)
                    self.queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[-] Error escribiendo telemetría en disco: {e}")
