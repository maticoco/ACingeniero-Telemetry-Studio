import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

class TelemetryProcessor:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self._clean_and_prepare()

    def _clean_and_prepare(self):
        """Prepara los datos brutos del CSV."""
        # Suavizado de señales ruidosas con media móvil (opcional)
        cols_to_smooth = ['steer_angle', 'brake_pct', 'throttle_pct', 'accG_long', 'accG_lat']
        for col in cols_to_smooth:
            if col in self.df.columns:
                self.df[f'{col}_smooth'] = self.df[col].rolling(window=3, min_periods=1, center=True).mean()

        # Tiempo en segundos
        if 'lap_time_ms' in self.df.columns:
            self.df['lap_time_s'] = self.df['lap_time_ms'] / 1000.0

        # Calcular dt (diferencia de tiempo entre frames)
        if 'timestamp_local' in self.df.columns:
            self.df['dt'] = self.df['timestamp_local'].diff().fillna(1/60.0) # asume 60hz fallback
        else:
            self.df['dt'] = 1/60.0
            
        # Limitar dt para evitar saltos enormes si se pausa el juego
        self.df['dt'] = self.df['dt'].clip(0, 0.5)

        # Calcular velocidad en m/s
        self.df['speed_ms'] = self.df['speed_kmh'] / 3.6
        
        # Calcular distancia recorrida diferencial (ds)
        self.df['ds'] = self.df['speed_ms'] * self.df['dt']

        # Inicializar columnas
        self.df['lap_distance'] = 0.0
        self.df['lap_pct'] = 0.0

        # Procesar por cada vuelta
        laps = self.df['lap'].unique()
        for lap in laps:
            mask = self.df['lap'] == lap
            lap_data = self.df.loc[mask]
            
            # Filtrar si estuvo parado mucho tiempo (opcional), pero para trackear distancia mejor integrar todo
            # Integración de la distancia (Suma acumulativa)
            dist_array = lap_data['ds'].cumsum().values
            self.df.loc[mask, 'lap_distance'] = dist_array
            
            # Normalización porcentual (Alineación Micro-Sectores)
            max_dist = dist_array[-1] if len(dist_array) > 0 and dist_array[-1] > 0 else 1.0
            self.df.loc[mask, 'lap_pct'] = (dist_array / max_dist) * 100.0

    def get_valid_laps(self):
        """Retorna una lista de vueltas validas (por ejemplo, donde se movió el coche)."""
        valid_laps = []
        laps = self.df['lap'].unique()
        for lap in laps:
            lap_df = self.df[self.df['lap'] == lap]
            max_speed = lap_df['speed_kmh'].max()
            # Asumimos que si no pasó de 50km/h fue una vuelta parada o inválida
            if max_speed > 50:
                valid_laps.append(lap)
        return sorted(valid_laps)

    def get_lap_data(self, lap_number):
        """Retorna el DataFrame de una vuelta específica."""
        return self.df[self.df['lap'] == lap_number].copy()
    
    def get_lap_time(self, lap_number):
        """Retorna el tiempo de la vuelta en formato string (M:SS.mmm)."""
        lap_df = self.get_lap_data(lap_number)
        if len(lap_df) == 0:
            return "0:00.000"
            
        time_s = lap_df['lap_time_s'].max()
        minutes = int(time_s // 60)
        seconds = time_s % 60
        return f"{minutes}:{seconds:06.3f}"
        
    def get_summary(self):
        """Retorna un resumen global."""
        return {
            'total_laps': len(self.get_valid_laps()),
            'max_speed': self.df['speed_kmh'].max(),
            'max_lat_g': self.df['accG_lat'].abs().max(),
            'max_long_g': self.df['accG_long'].abs().max()
        }
