import socket
import json
from telemetry_standalone.trigger_manager import TriggerManager
from telemetry_standalone.recorder import TelemetryRecorder

class TelemetryListener:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Permite reutilizar el puerto
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        
        # Instancia el módulo lógico
        self.trigger_manager = TriggerManager()
        
        # Instancia el módulo de grabación
        self.recorder = TelemetryRecorder()
        
    def set_event_callback(self, callback):
        """Registra la función del Agente IA que va a recibir los eventos importantes."""
        self.trigger_manager.on_event(callback)

    def start(self):
        """Inicia el bucle infinito de escucha de telemetría a 60Hz."""
        print(f"[*] Escuchando telemetría UDP (SimHub/Mock) en {self.host}:{self.port}...")
        self.recorder.start()
        try:
            while True:
                # Recibe el paquete UDP
                data, addr = self.sock.recvfrom(4096)
                
                try:
                    # Convierte el JSON a un diccionario de Python
                    telemetry_dict = json.loads(data.decode('utf-8'))
                    
                    # Delega la evaluación de los triggers al manager
                    self.trigger_manager.evaluate(telemetry_dict)
                    
                    # Graba la telemetría en disco
                    self.recorder.record(telemetry_dict)
                    
                except json.JSONDecodeError:
                    print("[-] Error decodificando el paquete JSON.")
                except Exception as e:
                    print(f"[-] Error procesando telemetría: {e}")
                    
        except KeyboardInterrupt:
            print("\n[*] Listener detenido por el usuario.")
        finally:
            self.recorder.stop()
            self.sock.close()

if __name__ == "__main__":
    # Callback de prueba para imprimir los eventos por consola
    def print_event(event_type, msg):
        print(f"\n[>>> EVENTO DISPARADO <<<] {event_type} - {msg}\n")

    # Instanciamos y arrancamos
    listener = TelemetryListener()
    listener.set_event_callback(print_event)
    listener.start()
