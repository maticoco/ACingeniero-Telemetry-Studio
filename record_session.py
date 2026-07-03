import sys
import os

# Aseguramos que Python pueda importar los módulos desde la carpeta local telemetry_standalone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    print("=====================================================")
    print("  🏁 ACingeniero - Grabador de Telemetría Pura 🏁  ")
    print("=====================================================")
    print("Este grabador extraerá datos masivos (Suspensiones,")
    print("Pedales, Fuerzas G, Temperaturas I-M-O) para tu")
    print("Entrenador IA y tu Ingeniero de Pista.")
    print("=====================================================\n")

def main():
    print_banner()
    print("\n[+] Iniciando módulo Assetto Corsa...")
    from telemetry_standalone.ac_shm import ACSharedMemoryListener
    listener = ACSharedMemoryListener()
    listener.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Sesión de grabación terminada manualmente.")
