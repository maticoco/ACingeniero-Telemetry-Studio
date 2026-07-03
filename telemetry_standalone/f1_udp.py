import socket
import struct
import time
from telemetry_standalone.base_listener import BaseTelemetryListener

class F1UDPListener(BaseTelemetryListener):
    """
    Oyente de Telemetría UDP para la saga F1 de Codemasters/EA (F1 23/24/25).
    Intercepta paquetes de red binarios y los decodifica.
    """
    def __init__(self, host="127.0.0.1", port=20777):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        
        # Diccionario para almacenar los últimos datos extraídos
        self.current_data = {
            "player_car_index": 0,
            "session_type": "Unknown",
            "track_name": "Unknown",
            "last_event": "None",
            "track_temp": 0.0,
            "air_temp": 0.0,
            "lap": 0,
            "position": 0,
            "speed_kmh": 0.0,
            "throttle": 0.0,
            "steer": 0.0,
            "brake": 0.0,
            "gear": 0,
            "rpm": 0,
            "ers_percent": 0.0,
            "temp_fl": 0.0,
            "temp_fr": 0.0,
            "temp_rl": 0.0,
            "temp_rr": 0.0,
            "fuel_l": 0.0,
            "tyre_compound": "Unknown",
            "damage_aero": 0.0,
            "damage_engine": 0.0,
            "lap_completed": False,
            
            # --- Entrenador (Blueprint) ---
            "throttle_pct": 0.0,
            "brake_pct": 0.0,
            "steer_angle": 0.0,
            "lap_time_ms": 0,
            "sector_1_ms": 0,
            "sector_2_ms": 0,
            "delta_ms": 0.0,
            "accG_long": 0.0,
            "accG_lat": 0.0,
            "pos_x": 0.0,
            "pos_y": 0.0,
            "pos_z": 0.0,

            # --- Ingeniero (Blueprint) ---
            "susp_travel_fl": 0.0, "susp_travel_fr": 0.0, "susp_travel_rl": 0.0, "susp_travel_rr": 0.0,
            "susp_velocity_fl": 0.0, "susp_velocity_fr": 0.0, "susp_velocity_rl": 0.0, "susp_velocity_rr": 0.0,
            "wheel_slip_fl": 0.0, "wheel_slip_fr": 0.0, "wheel_slip_rl": 0.0, "wheel_slip_rr": 0.0,
            "tyre_temp_inner_fl": 0.0, "tyre_temp_inner_fr": 0.0, "tyre_temp_inner_rl": 0.0, "tyre_temp_inner_rr": 0.0,
            "tyre_temp_middle_fl": 0.0, "tyre_temp_middle_fr": 0.0, "tyre_temp_middle_rl": 0.0, "tyre_temp_middle_rr": 0.0,
            "tyre_temp_outer_fl": 0.0, "tyre_temp_outer_fr": 0.0, "tyre_temp_outer_rl": 0.0, "tyre_temp_outer_rr": 0.0,
            "tyre_pressure_fl": 0.0, "tyre_pressure_fr": 0.0, "tyre_pressure_rl": 0.0, "tyre_pressure_rr": 0.0,
            "brake_temp_fl": 0.0, "brake_temp_fr": 0.0, "brake_temp_rl": 0.0, "brake_temp_rr": 0.0,
            "drs_active": 0.0
        }

    def start(self):
        """Inicia el socket UDP y comienza el loop de lectura binaria."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(2.0)
            print(f"\n[*] Conectando a F1 25 (UDP: {self.host}:{self.port})...")
            self._running = True
            self.recorder.start()
            print("[+] ¡Escucha de red iniciada correctamente! Esperando telemetría...")

            self._listen_loop()

        except Exception as e:
            print(f"[-] Error iniciando lector UDP F1: {e}")
            self.stop()
        finally:
            if self.sock:
                self.sock.close()
            print("[*] Conexión de red de F1 25 cerrada.")

    def _listen_loop(self):
        """Bucle principal de recepción y enrutamiento de paquetes."""
        while self._running:
            try:
                data, _ = self.sock.recvfrom(2048) # F1 packets son < 1500 bytes
                self._process_packet(data)
            except socket.timeout:
                # Si el juego está en pausa o cerrado, el socket expira cada 2s.
                # No es un error fatal, simplemente volvemos al while.
                continue
            except Exception as e:
                print(f"[-] Error procesando paquete F1 UDP: {e}")

    def _process_packet(self, data: bytes):
        """
        Interpreta el Header estándar de F1 (29 bytes) para saber de qué tipo
        de paquete se trata y mandarlo al parser específico.
        """
        # HEADER FORMAT F1 2023/24/25: (29 Bytes)
        # H(2) format, B(1) gameYear, B(1) gameMajor, B(1) gameMinor, B(1) packetVersion, 
        # B(1) packetId, Q(8) sessionUID, f(4) sessionTime, I(4) frameIdentifier,
        # I(4) overallFrame, B(1) playerCarIndex, B(1) secondaryPlayerCarIndex
        header_format = "<HBBBBBQfIIBB"
        header_size = struct.calcsize(header_format)
        
        if len(data) < header_size:
            return

        header = struct.unpack_from(header_format, data, 0)
        packet_id = header[5]
        player_car_index = header[10]

        # Guardamos el índice del auto del jugador para usarlo al parsear arrays
        self.current_data["player_car_index"] = player_car_index

        # Enrutador de paquetes (FASE 3 se encargará de los contenidos)
        if packet_id == 0:
            self._parse_motion_packet(data, header_size)
        elif packet_id == 1:
            self._parse_session_packet(data, header_size)
        elif packet_id == 2:
            self._parse_lap_data_packet(data, header_size)
        elif packet_id == 3:
            self._parse_event_packet(data, header_size)
        elif packet_id == 6:
            self._parse_telemetry_packet(data, header_size)
        elif packet_id == 7:
            self._parse_status_packet(data, header_size)
        elif packet_id == 10:
            self._parse_damage_packet(data, header_size)

    # =========================================================================
    # FASE 3: Parseo binario por paquete (Decodificación F1 23/24)
    # =========================================================================
    def _parse_motion_packet(self, data, offset):
        """Packet 0: Dinámica y Suspensión (Fuerzas G, XYZ, Amortiguación)"""
        player_idx = self.current_data["player_car_index"]
        # CarMotionData array is at offset, 60 bytes each.
        car_size = 60
        p_offset = offset + (player_idx * car_size)
        
        try:
            # worldPositionX, worldPositionY, worldPositionZ (offset 0, 3 floats)
            posX, posY, posZ = struct.unpack_from("<fff", data, p_offset)
            self.current_data["pos_x"] = posX
            self.current_data["pos_y"] = posY
            self.current_data["pos_z"] = posZ
            
            # gForceLateral, gForceLongitudinal, gForceVertical are at offset + (22 * 60) + player specific data
            # Actually in F1 23/24, Extra Player Car Data is after the 22 CarMotionData array
            extra_data_offset = offset + (22 * 60)
            
            # suspensionPosition (4 floats), suspensionVelocity (4 floats), suspensionAcceleration (4 floats)
            susp_pos = struct.unpack_from("<ffff", data, extra_data_offset)
            self.current_data["susp_travel_rl"] = susp_pos[0]
            self.current_data["susp_travel_rr"] = susp_pos[1]
            self.current_data["susp_travel_fl"] = susp_pos[2]
            self.current_data["susp_travel_fr"] = susp_pos[3]
            
            susp_vel = struct.unpack_from("<ffff", data, extra_data_offset + 16)
            self.current_data["susp_velocity_rl"] = susp_vel[0]
            self.current_data["susp_velocity_rr"] = susp_vel[1]
            self.current_data["susp_velocity_fl"] = susp_vel[2]
            self.current_data["susp_velocity_fr"] = susp_vel[3]
            
            # wheelSlip (4 floats) at offset + 64 from extra_data
            wheel_slip = struct.unpack_from("<ffff", data, extra_data_offset + 64)
            self.current_data["wheel_slip_rl"] = wheel_slip[0]
            self.current_data["wheel_slip_rr"] = wheel_slip[1]
            self.current_data["wheel_slip_fl"] = wheel_slip[2]
            self.current_data["wheel_slip_fr"] = wheel_slip[3]
            
            # gForce (lateral, longitudinal, vertical) at offset + 104 from extra_data
            g_forces = struct.unpack_from("<fff", data, extra_data_offset + 104)
            self.current_data["accG_lat"] = g_forces[0]
            self.current_data["accG_long"] = g_forces[1]
            
        except Exception as e:
            print(f"[-] Error parseando MOTION (Packet 0): {e}")

    def _parse_session_packet(self, data, offset):
        """Packet 1: Datos de sesión (Clima, Temperatura, Tipo)"""
        # SessionType está a 6 bytes del inicio del payload.
        # Format: weather(uint8), trackTemp(int8), airTemp(int8), totalLaps(uint8), trackLength(uint16), sessionType(uint8), trackId(int8)
        try:
            weather, track_temp, air_temp, total_laps, track_length, session_type, track_id = struct.unpack_from("<BbbBHBb", data, offset)
            self.current_data["track_temp"] = float(track_temp)
            self.current_data["air_temp"] = float(air_temp)
            
            # Mapeo de Pista
            tracks = {0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai", 3: "Sakhir (Bahrain)", 4: "Catalunya", 5: "Monaco", 6: "Montreal", 7: "Silverstone", 8: "Hockenheim", 9: "Hungaroring", 10: "Spa", 11: "Monza", 12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi", 15: "Texas", 16: "Brazil", 17: "Austria", 18: "Sochi", 19: "Mexico", 20: "Baku", 21: "Sakhir Short", 22: "Silverstone Short", 23: "Texas Short", 24: "Suzuka Short", 25: "Hanoi", 26: "Zandvoort", 27: "Imola", 28: "Portimao", 29: "Jeddah", 30: "Miami", 31: "Las Vegas", 32: "Losail (Qatar)"}
            self.current_data["track_name"] = tracks.get(track_id, "Unknown Track")
            
            # Tipos de sesión: 1=P1, 2=P2, 3=P3, 4=Short P, 5=Q1, 6=Q2, 7=Q3, 10=Race
            session_map = {1:"Practice 1", 2:"Practice 2", 3:"Practice 3", 5:"Qualy 1", 6:"Qualy 2", 7:"Qualy 3", 10:"Race"}
            self.current_data["session_type"] = session_map.get(session_type, "Unknown")
        except Exception as e:
            print(f"[-] Error parseando SESSION (Packet 1): {e}")

    def _parse_event_packet(self, data, offset):
        """Packet 3: Eventos en pista (Choques, Penalizaciones, Fin de sesión)"""
        try:
            event_code = struct.unpack_from("4s", data, offset)[0]
            code_str = event_code.decode('ascii', errors='ignore')
            
            event_map = {
                "SSTA": "Session Started",
                "SEND": "Session Ended",
                "FTLP": "Fastest Lap",
                "RETF": "Retirement",
                "DRSE": "DRS Enabled",
                "DRSD": "DRS Disabled",
                "CHQF": "Chequered Flag",
                "PENA": "Penalty Issued",
                "COLI": "Collision Detected!",
                "OVTK": "Overtake"
            }
            if code_str in event_map:
                self.current_data["last_event"] = event_map[code_str]
                self.trigger_manager.evaluate(self.current_data)
        except Exception as e:
            print(f"[-] Error parseando EVENT (Packet 3): {e}")

    def _parse_lap_data_packet(self, data, offset):
        """Packet 2: Datos de Vuelta (Posición, Sectores, Final de Vuelta)"""
        lap_size = 50
        player_idx = self.current_data["player_car_index"]
        
        try:
            # 1. Leer datos del jugador
            p_offset = offset + (player_idx * lap_size)
            # Offset 14 (uint16): delta to car in front in MS. Offset 30 (uint8): car position. Offset 31 (uint8): current lap.
            delta_front_ms = struct.unpack_from("<H", data, p_offset + 14)[0]
            player_pos = struct.unpack_from("<B", data, p_offset + 30)[0]
            current_lap = struct.unpack_from("<B", data, p_offset + 31)[0]
            
            self.current_data["position"] = player_pos
            # Si es mayor a 60 seg, ignorarlo (suele ser 0xFFFF cuando no aplica)
            self.current_data["rival_ahead_gap"] = delta_front_ms / 1000.0 if delta_front_ms < 60000 else 0.0
            
            if current_lap > self.current_data["lap"] and self.current_data["lap"] > 0:
                self.current_data["lap_completed"] = True
            else:
                self.current_data["lap_completed"] = False
            self.current_data["lap"] = current_lap

            # 2. Buscar rivales en la cuadrícula
            rival_ahead_idx = -1
            rival_behind_idx = -1
            self.current_data["rival_behind_gap"] = 0.0

            for i in range(22):
                if i == player_idx: continue
                c_offset = offset + (i * lap_size)
                c_pos = struct.unpack_from("<B", data, c_offset + 30)[0]
                
                if c_pos == player_pos - 1:
                    rival_ahead_idx = i
                elif c_pos == player_pos + 1:
                    rival_behind_idx = i
                    c_delta = struct.unpack_from("<H", data, c_offset + 14)[0]
                    self.current_data["rival_behind_gap"] = c_delta / 1000.0 if c_delta < 60000 else 0.0

            self.current_data["rival_ahead_idx"] = rival_ahead_idx
            self.current_data["rival_behind_idx"] = rival_behind_idx

        except Exception as e:
            print(f"[-] Error parseando LAP DATA (Packet 2): {e}")

    def _parse_telemetry_packet(self, data, offset):
        """Packet 6: Telemetría pura (Velocidad, Pedales, Tracción, Gomas)"""
        # Array de 22 CarTelemetryData. Cada uno pesa 60 bytes.
        car_size = 60
        player_idx = self.current_data["player_car_index"]
        p_offset = offset + (player_idx * car_size)
        
        try:
            # Struct: speed(uint16), throttle(float), steer(float), brake(float), clutch(uint8), gear(int8), engineRPM(uint16), drs(uint8)
            speed, throttle, steer, brake, clutch, gear, rpm, drs = struct.unpack_from("<HfffbBhB", data, p_offset)
            
            self.current_data["speed_kmh"] = float(speed)
            self.current_data["throttle_pct"] = throttle
            self.current_data["steer_angle"] = steer
            self.current_data["brake_pct"] = brake
            self.current_data["gear"] = gear
            self.current_data["rpm"] = rpm
            self.current_data["drs_active"] = drs
            
            # Temperaturas internas de neumáticos (offset 30 dentro del CarTelemetryData)
            # RL, RR, FL, FR (uint8 x 4)
            tyre_temps = struct.unpack_from("<BBBB", data, p_offset + 34) # 34 is surface temp, 38 is inner
            self.current_data["temp_rl"] = float(tyre_temps[0])
            self.current_data["temp_rr"] = float(tyre_temps[1])
            self.current_data["temp_fl"] = float(tyre_temps[2])
            self.current_data["temp_fr"] = float(tyre_temps[3])
            
            # Inner temps (uint8 x 4) at offset 38
            inner_temps = struct.unpack_from("<BBBB", data, p_offset + 38)
            self.current_data["tyre_temp_inner_rl"] = float(inner_temps[0])
            self.current_data["tyre_temp_inner_rr"] = float(inner_temps[1])
            self.current_data["tyre_temp_inner_fl"] = float(inner_temps[2])
            self.current_data["tyre_temp_inner_fr"] = float(inner_temps[3])
            
            # Tyre Pressures (float x 4) at offset 42
            pressures = struct.unpack_from("<ffff", data, p_offset + 42)
            self.current_data["tyre_pressure_rl"] = pressures[0]
            self.current_data["tyre_pressure_rr"] = pressures[1]
            self.current_data["tyre_pressure_fl"] = pressures[2]
            self.current_data["tyre_pressure_fr"] = pressures[3]
            
            # Brakes Temp (uint16 x 4) at offset 26
            brakes = struct.unpack_from("<HHHH", data, p_offset + 26)
            self.current_data["brake_temp_rl"] = float(brakes[0])
            self.current_data["brake_temp_rr"] = float(brakes[1])
            self.current_data["brake_temp_fl"] = float(brakes[2])
            self.current_data["brake_temp_fr"] = float(brakes[3])

            # Disparamos evaluación en el TriggerManager
            self.trigger_manager.evaluate(self.current_data)
            
            # Grabamos todo en CSV a 60Hz usando este paquete como master clock
            self.recorder.record(self.current_data)
            
        except Exception as e:
            print(f"[-] Error parseando TELEMETRY (Packet 6): {e}")

    def _parse_status_packet(self, data, offset):
        """Packet 7: Estado del vehículo (Combustible, ERS, Compuesto)"""
        status_size = 71
        player_idx = self.current_data["player_car_index"]
        
        try:
            compounds = {16:"Soft", 17:"Medium", 18:"Hard", 7:"Inters", 8:"Wet"}

            for i in range(22):
                p_offset = offset + (i * status_size)
                # Visual Tyre Compound está en el byte 22
                tyre_visual = struct.unpack_from("<B", data, p_offset + 22)[0]
                compound_name = compounds.get(tyre_visual, "Unknown")
                
                if i == player_idx:
                    # Fuel está a 5 bytes del inicio del CarStatusData (float)
                    fuel = struct.unpack_from("<f", data, p_offset + 5)[0]
                    self.current_data["fuel_l"] = fuel
                    self.current_data["tyre_compound"] = compound_name
                    
                    # ERS Store Energy está en el byte 27 (float 4 bytes)
                    ers_energy = struct.unpack_from("<f", data, p_offset + 27)[0]
                    self.current_data["ers_percent"] = (ers_energy / 4000000.0) * 100.0
                    
                elif i == self.current_data.get("rival_ahead_idx", -1):
                    self.current_data["rival_ahead_tyre"] = compound_name
                    
                elif i == self.current_data.get("rival_behind_idx", -1):
                    self.current_data["rival_behind_tyre"] = compound_name

        except Exception as e:
            print(f"[-] Error parseando STATUS (Packet 7): {e}")

    def _parse_damage_packet(self, data, offset):
        """Packet 10: Daños estructurales"""
        # Array de 22 CarDamageData. Tamaño aprox 42 bytes.
        damage_size = 42
        player_idx = self.current_data["player_car_index"]
        p_offset = offset + (player_idx * damage_size)
        
        try:
            # Front Left Wing (byte 24), Front Right Wing (byte 25), Engine (byte 36)
            fl_wing, fr_wing = struct.unpack_from("<BB", data, p_offset + 24)
            engine = struct.unpack_from("<B", data, p_offset + 36)[0]
            
            # Normalizar a 0.0 - 1.0 para nuestro bot
            self.current_data["damage_aero"] = max(fl_wing, fr_wing) / 100.0
            self.current_data["damage_engine"] = engine / 100.0
        except Exception as e:
            print(f"[-] Error parseando DAMAGE (Packet 10): {e}")
