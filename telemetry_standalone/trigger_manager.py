import time

class TriggerManager:
    def __init__(self):
        # Estado interno para mantener un registro en el tiempo (historial de variables)
        self.state = {
            "temp_fl_high_start": None,
            "last_lap_completed": False,
            "fuel_warning_triggered": False,
            "damage_warning_triggered": False,
        }
        self.callbacks = []
        self.last_telemetry = {}

    def get_last_telemetry(self) -> dict:
        """Devuelve el último paquete de telemetría recibido para dar contexto."""
        return self.last_telemetry

    def on_event(self, callback):
        """Registra una función que será llamada cuando se dispare un evento."""
        self.callbacks.append(callback)

    def _emit(self, event_type, message):
        """Dispara un evento llamando a todos los callbacks registrados."""
        for cb in self.callbacks:
            cb(event_type, message)

    def evaluate(self, telemetry: dict):
        """
        Evalúa el payload de telemetría y dispara eventos basados en reglas lógicas.
        """
        self.last_telemetry = telemetry
        current_time = time.time()

        # 1. Trigger de temperatura de neumático FL (>112°C por > 3 seg)
        temp_fl = telemetry.get("temp_fl", 0)
        if temp_fl > 112:
            if self.state["temp_fl_high_start"] is None:
                self.state["temp_fl_high_start"] = current_time
            elif current_time - self.state["temp_fl_high_start"] > 3.0:
                self._emit("SOBRECALENTAMIENTO_NEUMATICO_FL", f"Temperatura goma delantera izquierda crítica: {temp_fl:.1f}°C")
                # Establecer un cooldown artificial (10 seg) para no hacer spam del mismo trigger
                self.state["temp_fl_high_start"] = current_time + 10.0 
        else:
            self.state["temp_fl_high_start"] = None

        # 2. Trigger de fin de vuelta
        lap_completed = telemetry.get("lap_completed", False)
        if lap_completed and not self.state["last_lap_completed"]:
            self._emit("FIN_DE_VUELTA", "Vuelta completada.")
        self.state["last_lap_completed"] = lap_completed

        # 3. Trigger de bajo combustible (< 5 L)
        fuel = telemetry.get("fuel_l", 100)
        if fuel < 5.0 and not self.state["fuel_warning_triggered"]:
            self._emit("BAJO_COMBUSTIBLE", f"Nivel de combustible crítico: {fuel:.1f} litros restantes.")
            self.state["fuel_warning_triggered"] = True
        elif fuel >= 5.0:
            self.state["fuel_warning_triggered"] = False

        # 4. Trigger de daño detectado
        damage = telemetry.get("damage_engine", 0) + telemetry.get("damage_aero", 0)
        if damage > 0.1 and not self.state["damage_warning_triggered"]:
            self._emit("DAÑO_DETECTADO", "Daño mecánico o aerodinámico detectado en el monoplaza.")
            self.state["damage_warning_triggered"] = True
        elif damage == 0:
            self.state["damage_warning_triggered"] = False
