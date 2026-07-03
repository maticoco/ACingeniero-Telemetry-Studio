import ctypes
import mmap
import time
from telemetry_standalone.base_listener import BaseTelemetryListener

# --- Estructuras de Memoria Compartida de Assetto Corsa ---
class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int32),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int32),
        ("rpms", ctypes.c_int32),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int32),
        ("pitLimiterOn", ctypes.c_int32),
        ("abs", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("autoShifterOn", ctypes.c_int32),
        ("rideHeight", ctypes.c_float * 2),
        ("turboBoost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("airDensity", ctypes.c_float),
        ("airTemp", ctypes.c_float),
        ("roadTemp", ctypes.c_float),
        ("localAngularVel", ctypes.c_float * 3),
        ("finalFF", ctypes.c_float),
        ("performanceMeter", ctypes.c_float),
        ("engineBrake", ctypes.c_int32),
        ("ersRecoveryLevel", ctypes.c_int32),
        ("ersPowerLevel", ctypes.c_int32),
        ("ersHeatCharging", ctypes.c_int32),
        ("ersIsCharging", ctypes.c_int32),
        ("kersCurrentKJ", ctypes.c_float),
        ("drsAvailable", ctypes.c_int32),
        ("drsEnabled", ctypes.c_int32),
        ("brakeTemp", ctypes.c_float * 4),
        ("clutch", ctypes.c_float),
        ("tyreTempI", ctypes.c_float * 4),
        ("tyreTempM", ctypes.c_float * 4),
        ("tyreTempO", ctypes.c_float * 4),
    ]

class SPageFileGraphic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int32),
        ("status", ctypes.c_int32),
        ("session", ctypes.c_int32),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int32),
        ("position", ctypes.c_int32),
        ("iCurrentTime", ctypes.c_int32),
        ("iLastTime", ctypes.c_int32),
        ("iBestTime", ctypes.c_int32),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int32),
        ("currentSectorIndex", ctypes.c_int32),
        ("lastSectorTime", ctypes.c_int32),
        ("numberOfLaps", ctypes.c_int32),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
        # ("activeCars", ctypes.c_int32), # Eliminado para corregir el desfase de 4 bytes en carCoordinates
        ("carCoordinates", ctypes.c_float * 3),
    ]

class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int32),
        ("numCars", ctypes.c_int32),
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
        ("playerName", ctypes.c_wchar * 33),
        ("playerSurname", ctypes.c_wchar * 33),
        ("playerNick", ctypes.c_wchar * 33),
        ("sectorCount", ctypes.c_int32),
        ("maxTorque", ctypes.c_float),
        ("maxPower", ctypes.c_float),
        ("maxRpm", ctypes.c_int32),
        ("maxFuel", ctypes.c_float),
        ("suspensionMaxTravel", ctypes.c_float * 4),
        ("tyreRadius", ctypes.c_float * 4),
        ("maxTurboBoost", ctypes.c_float),
        ("airTemp", ctypes.c_float),
        ("roadTemp", ctypes.c_float),
        ("penaltiesEnabled", ctypes.c_int32),
        ("aidFuelRate", ctypes.c_float),
        ("aidTireRate", ctypes.c_float),
        ("aidMechanicalDamage", ctypes.c_float),
        ("allowTyreBlankets", ctypes.c_int32),
        ("aidStability", ctypes.c_float),
        ("aidAutoClutch", ctypes.c_int32),
        ("aidAutoBlip", ctypes.c_int32),
        ("hasDRS", ctypes.c_int32),
        ("hasERS", ctypes.c_int32),
        ("hasKERS", ctypes.c_int32),
        ("kersMaxJ", ctypes.c_float),
        ("engineBrakeSettingsCount", ctypes.c_int32),
        ("ersPowerControllerCount", ctypes.c_int32),
        ("trackSPlineLength", ctypes.c_float),
        ("trackConfiguration", ctypes.c_wchar * 33),
    ]

AC_SESSION_TYPES = {0: "Unknown", 1: "Practice", 2: "Qualify", 3: "Race", 4: "Hotlap", 5: "Time Attack", 6: "Drift", 7: "Drag"}

class ACSharedMemoryListener(BaseTelemetryListener):
    def __init__(self):
        super().__init__()
        self._last_completed_laps = -1

    def start(self):
        print("\n[*] Conectando directamente al cerebro de Assetto Corsa (Shared Memory)...")
        self._running = True
        self.recorder.start()
        
        try:
            shm_physics = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics), "Local\\acpmf_physics")
            physics = SPageFilePhysics.from_buffer(shm_physics)
            
            shm_graphics = mmap.mmap(0, ctypes.sizeof(SPageFileGraphic), "Local\\acpmf_graphics")
            graphics = SPageFileGraphic.from_buffer(shm_graphics)
            
            shm_static = mmap.mmap(0, ctypes.sizeof(SPageFileStatic), "Local\\acpmf_static")
            static = SPageFileStatic.from_buffer(shm_static)
            
            track_name = str(static.track).rstrip('\x00')
            car_model = str(static.carModel).rstrip('\x00')
            
            print("[+] ¡Conexión exitosa! Extrayendo Blueprint Pura a 60Hz.")
            
            while self._running:
                current_laps = graphics.completedLaps
                lap_completed = False
                if self._last_completed_laps != -1 and current_laps > self._last_completed_laps:
                    lap_completed = True
                self._last_completed_laps = current_laps

                telemetry_dict = {
                    # --- METADATA ---
                    "track": track_name,
                    "car_model": car_model,
                    
                    # --- COACH IA (Pilotaje) ---
                    "throttle_pct": float(physics.gas),
                    "brake_pct": float(physics.brake),
                    "abs_active": float(physics.abs),
                    "tc_active": float(physics.tc),
                    "steer_angle": float(physics.steerAngle),
                    "speed_kmh": float(physics.speedKmh),
                    "gear": int(physics.gear) - 1, 
                    "rpm": int(physics.rpms),
                    "accG_long": float(physics.accG[2]), # Longitudinal
                    "accG_lat": float(physics.accG[0]), # Lateral
                    "pos_x": float(graphics.carCoordinates[0]),
                    "pos_y": float(graphics.carCoordinates[1]),
                    "pos_z": float(graphics.carCoordinates[2]),
                    "lap": int(graphics.completedLaps),
                    "lap_time_ms": int(graphics.iCurrentTime),
                    "lap_completed": lap_completed,

                    # --- INGENIERO DE PISTA (Físicas & Setup) ---
                    "ride_height_f": float(physics.rideHeight[0]),
                    "ride_height_r": float(physics.rideHeight[1]),
                    "susp_travel_fl": float(physics.suspensionTravel[0]),
                    "susp_travel_fr": float(physics.suspensionTravel[1]),
                    "susp_travel_rl": float(physics.suspensionTravel[2]),
                    "susp_travel_rr": float(physics.suspensionTravel[3]),
                    "wheel_load_fl": float(physics.wheelLoad[0]),
                    "wheel_load_fr": float(physics.wheelLoad[1]),
                    "wheel_load_rl": float(physics.wheelLoad[2]),
                    "wheel_load_rr": float(physics.wheelLoad[3]),
                    "wheel_slip_fl": float(physics.wheelSlip[0]),
                    "wheel_slip_fr": float(physics.wheelSlip[1]),
                    "wheel_slip_rl": float(physics.wheelSlip[2]),
                    "wheel_slip_rr": float(physics.wheelSlip[3]),
                    
                    "tyre_temp_inner_fl": float(physics.tyreTempI[0]),
                    "tyre_temp_middle_fl": float(physics.tyreTempM[0]),
                    "tyre_temp_outer_fl": float(physics.tyreTempO[0]),
                    "tyre_temp_inner_fr": float(physics.tyreTempI[1]),
                    "tyre_temp_middle_fr": float(physics.tyreTempM[1]),
                    "tyre_temp_outer_fr": float(physics.tyreTempO[1]),
                    "tyre_temp_inner_rl": float(physics.tyreTempI[2]),
                    "tyre_temp_middle_rl": float(physics.tyreTempM[2]),
                    "tyre_temp_outer_rl": float(physics.tyreTempO[2]),
                    "tyre_temp_inner_rr": float(physics.tyreTempI[3]),
                    "tyre_temp_middle_rr": float(physics.tyreTempM[3]),
                    "tyre_temp_outer_rr": float(physics.tyreTempO[3]),

                    "tyre_pressure_fl": float(physics.wheelsPressure[0]),
                    "tyre_pressure_fr": float(physics.wheelsPressure[1]),
                    "tyre_pressure_rl": float(physics.wheelsPressure[2]),
                    "tyre_pressure_rr": float(physics.wheelsPressure[3]),

                    "tyre_wear_fl": float(physics.tyreWear[0]),
                    "tyre_wear_fr": float(physics.tyreWear[1]),
                    "tyre_wear_rl": float(physics.tyreWear[2]),
                    "tyre_wear_rr": float(physics.tyreWear[3]),

                    "brake_temp_fl": float(physics.brakeTemp[0]),
                    "brake_temp_fr": float(physics.brakeTemp[1]),
                    "brake_temp_rl": float(physics.brakeTemp[2]),
                    "brake_temp_rr": float(physics.brakeTemp[3]),

                    "fuel_l": float(physics.fuel),
                    "drs_active": float(physics.drs),
                    "ers_percent": float(physics.kersCharge),
                    "damage_engine": float(physics.carDamage[4]),
                    "damage_aero": float(physics.carDamage[0]), 
                }

                # Enviar a lógica y grabación
                self.trigger_manager.evaluate(telemetry_dict)
                self.recorder.record(telemetry_dict)
                
                time.sleep(1.0 / 60.0)

        except Exception as e:
            print(f"[-] Error crítico leyendo memoria de AC: {e}")
            print("    ¿Está Assetto Corsa abierto y corriendo?")
        finally:
            self.stop()
            print("[*] Lector de telemetría de Assetto Corsa detenido.")
