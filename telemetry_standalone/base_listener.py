from abc import ABC, abstractmethod
from telemetry_standalone.trigger_manager import TriggerManager
from telemetry_standalone.recorder import TelemetryRecorder

class BaseTelemetryListener(ABC):
    """
    Clase abstracta (Interfaz) para los oyentes de telemetría.
    Implementa el Principio de Inversión de Dependencias (SOLID) asegurando que
    cualquier simulador (AC, F1 25, etc) exponga la misma API al resto del sistema.
    """
    def __init__(self):
        self.trigger_manager = TriggerManager()
        self.recorder = TelemetryRecorder()
        self._running = False

    def set_event_callback(self, callback):
        """
        Conecta la función de callback del ingeniero a los eventos
        que dispara el administrador de triggers.
        """
        self.trigger_manager.on_event(callback)

    @abstractmethod
    def start(self):
        """
        Inicia el bucle de lectura del simulador. 
        Debe implementarse en las clases hijas.
        """
        pass

    def stop(self):
        """
        Detiene el lector de telemetría y frena las grabaciones.
        """
        self._running = False
        self.recorder.stop()
