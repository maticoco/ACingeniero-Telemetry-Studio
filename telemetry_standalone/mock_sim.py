import socket
import json
import time
import random

def run_mock():
    host = '127.0.0.1'
    port = 9999
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"[*] Iniciando simulador de telemetría hacia {host}:{port}")
    print("[*] El simulador enviará datos a 60Hz. Eventos programados:")
    print("    - 2 segundos: Sobrecalentamiento goma delantera izquierda.")
    print("    - 5 segundos: Combustible bajo.")
    print("    - 7.5 segundos: Fin de vuelta.")
    print("    - 9 segundos: Daño detectado.")
    print("[*] Presiona Ctrl+C para detener.")
    print("-" * 50)
    
    # Payload base (Mock normal)
    base_telemetry = {
        "speed_kmh": 250.0,
        "gear": 6,
        "rpm": 11000,
        "temp_fl": 90.0,
        "temp_fr": 90.0,
        "temp_rl": 95.0,
        "temp_rr": 95.0,
        "fuel_l": 15.0,
        "lap_completed": False,
        "damage_engine": 0.0,
        "damage_aero": 0.0
    }

    try:
        # Loop principal de simulación (infinito a 60Hz)
        tick = 1
        while True:
            # Copiamos el payload base
            telemetry = base_telemetry.copy()
            
            # Evento 1: Simular sobrecalentamiento (>112C)
            if tick > 120: # A partir de los 2 seg.
                telemetry["temp_fl"] = 115.0 + random.uniform(0, 2)
                
            # Evento 2: Simular bajo combustible (<5L)
            if tick > 300: # A partir de los 5 seg.
                telemetry["fuel_l"] = 4.5
                
            # Evento 3: Simular fin de vuelta (solo un instante)
            if tick == 450: # A los 7.5 seg.
                telemetry["lap_completed"] = True
                
            # Evento 4: Simular daño
            if tick > 540: # A los 9 seg.
                telemetry["damage_aero"] = 0.5
                
            # Enviar por UDP
            payload = json.dumps(telemetry).encode('utf-8')
            sock.sendto(payload, (host, port))
            
            # Esperar 1/60s para simular 60Hz
            time.sleep(1/60.0) 
            tick += 1
            
    except KeyboardInterrupt:
        print("\n[*] Simulador detenido por el usuario.")
    finally:
        sock.close()
        print("[*] Simulación finalizada.")

if __name__ == "__main__":
    run_mock()
