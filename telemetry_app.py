import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from telemetry_standalone.core_processor import TelemetryProcessor

st.set_page_config(page_title="ACingeniero Telemetry Studio", layout="wide")

# ==========================================
# 1. SIDEBAR & DATA MODEL (MULTI-VUELTA)
# ==========================================
import subprocess

# Inicialización del Session State
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'recorder_process' not in st.session_state:
    st.session_state.recorder_process = None
if 'save_dir' not in st.session_state:
    st.session_state.save_dir = "./data/sessions"
if 'sim_choice' not in st.session_state:
    st.session_state.sim_choice = "1"

if 'themes' not in st.session_state:
    st.session_state.themes = [
        {"slot": 1, "name": "Base (Vuelta 1)", "base_color": "#00BFFF", "brake_color": "#FF00FF", "dash": "solid", "gradient": ['#FF00FF', '#DDDDDD', '#00BFFF']},
        {"slot": 2, "name": "Comp. Primaria (Vuelta 2)", "base_color": "#00FF00", "brake_color": "#FF0000", "dash": "solid", "gradient": ['#FF0000', '#FF8C00', '#FFFF00', '#32CD32', '#00FF00']},
        {"slot": 3, "name": "Comp. Secundaria (Vuelta 3)", "base_color": "#FF8C00", "brake_color": "#8B4513", "dash": "dot", "gradient": ['#8B4513', '#CD853F', '#F4A460', '#FFA500', '#FF8C00']}
    ]

if 'track_rotation' not in st.session_state:
    st.session_state.track_rotation = -90
if 'invert_x' not in st.session_state:
    st.session_state.invert_x = False
if 'invert_z' not in st.session_state:
    st.session_state.invert_z = True

st.sidebar.title("🏁 ACingeniero Telemetry")
st.sidebar.subheader("Gestor Dinámico Multi-Vuelta")

# Listar archivos CSV en data/sessions/
data_dir = os.path.join(os.getcwd(), 'data', 'sessions')
if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)
csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
csv_names = [os.path.basename(f) for f in csv_files]

if not csv_names:
    st.sidebar.warning("No se encontraron sesiones. Graba una sesión primero.")
    st.stop()

@st.cache_data
def load_data(path):
    return TelemetryProcessor(path)

loaded_laps = []

# --- Lógica de Carga y Creación de Objetos "Vuelta" ---
for i in range(3):
    with st.sidebar.expander(f"🏎️ {st.session_state.themes[i]['name']}", expanded=(i==0)):
        
        session_options = ["Ninguna"] + csv_names
        default_index = len(csv_names) if i == 0 else 0 
        
        selected_csv = st.selectbox(f"Archivo de Sesión", session_options, index=default_index, key=f"session_{i}")
        
        if selected_csv != "Ninguna":
            csv_path = os.path.join(data_dir, selected_csv)
            processor = load_data(csv_path)
            valid_laps = processor.get_valid_laps()
            
            if valid_laps:
                selected_lap = st.selectbox(f"Número de Vuelta", valid_laps, index=len(valid_laps)-1 if i==0 else 0, key=f"lap_{i}")
                
                df = processor.get_lap_data(selected_lap)
                lap_time = processor.get_lap_time(selected_lap)
                
                lap_obj = {
                    "id": f"L{selected_lap}_S{i+1}",
                    "lap_num": selected_lap,
                    "dataframe": df,
                    "metadata": {
                        "time": lap_time,
                        "file": selected_csv,
                        "track": df['track'].iloc[0] if 'track' in df.columns else "Desconocido",
                        "car_model": df['car_model'].iloc[0] if 'car_model' in df.columns else "Desconocido"
                    },
                    "theme": st.session_state.themes[i]
                }
                loaded_laps.append(lap_obj)
                
                st.markdown(
                    f"<div style='border-left: 4px solid {st.session_state.themes[i]['base_color']}; padding-left: 10px; margin-top: 10px;'>"
                    f"<b style='color: {st.session_state.themes[i]['base_color']}; font-size: 1.1em;'>{lap_time}</b><br>"
                    f"<span style='font-size: 0.8em; color: #AAAAAA;'>Archivo: {selected_csv}</span><br>"
                    f"<span style='font-size: 0.8em; color: #AAAAAA;'>Trazada: {st.session_state.themes[i]['dash'].upper()}</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.warning("Sesión sin vueltas válidas.")

if not loaded_laps:
    st.sidebar.error("⚠️ Debes cargar al menos 1 vuelta para iniciar la telemetría.")
    st.stop()

# ==========================================
# 2. MAIN TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🚀 Driver Analysis", "🗺️ Track Map", "⚙️ Car Dynamics", "🛞 Tyres & Brakes", "🤖 AI Coach", "⚙️ Panel de Control", "🔴 Captura en Vivo"])

# --- TAB A: DRIVER ANALYSIS ---
with tab1:
    st.header("Análisis del Piloto", help="Compara los canales principales de telemetría sincronizados por distancia. El eje X compartido garantiza que comparemos el mismo metro de pista, no el tiempo.")
    
    # El Toggle de Visualización (UX/UI)
    view_mode = "Superpuesto"
    if len(loaded_laps) > 1:
        view_mode = st.radio("Modo de Visualización", ["Superpuesto", "Separado"], horizontal=True)
    
    x_col = 'lap_distance'
    
    if view_mode == "Superpuesto":
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=("Velocidad (km/h)", "Pedales (%)", "Ángulo de Volante (Rad)"))
        
        for lap in loaded_laps:
            df = lap['dataframe']
            theme = lap['theme']
            name = f"{lap['id']} - {lap['metadata']['time']}"
            
            fig.add_trace(go.Scatter(x=df[x_col], y=df['speed_kmh'], name=f'Vel: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df[x_col], y=df['throttle_pct_smooth'] * 100, name=f'Acel: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=2, col=1)
                                     
            fig.add_trace(go.Scatter(x=df[x_col], y=df['brake_pct_smooth'] * 100, name=f'Freno: {name}', 
                                     line=dict(color=theme['brake_color'], dash=theme['dash'], width=2)), row=2, col=1)
                                     
            fig.add_trace(go.Scatter(x=df[x_col], y=df['steer_angle_smooth'], name=f'Vol: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=3, col=1)

        fig.update_layout(height=800, paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', margin=dict(l=10, r=10, t=50, b=10))
        fig.update_yaxes(showgrid=True, gridcolor='#222222', zeroline=True, zerolinecolor='#333333')
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # Modo Separado (Split View)
        for lap in loaded_laps:
            st.subheader(f"🚗 Análisis: {lap['id']} ({lap['metadata']['time']})")
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                                subplot_titles=("Velocidad (km/h)", "Pedales (%)", "Ángulo de Volante (Rad)"))
            
            df = lap['dataframe']
            theme = lap['theme']
            name = f"{lap['id']}"
            
            fig.add_trace(go.Scatter(x=df[x_col], y=df['speed_kmh'], name=f'Vel: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df[x_col], y=df['throttle_pct_smooth'] * 100, name=f'Acel: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=2, col=1)
                                     
            fig.add_trace(go.Scatter(x=df[x_col], y=df['brake_pct_smooth'] * 100, name=f'Freno: {name}', 
                                     line=dict(color=theme['brake_color'], dash=theme['dash'], width=2)), row=2, col=1)
                                     
            fig.add_trace(go.Scatter(x=df[x_col], y=df['steer_angle_smooth'], name=f'Vol: {name}', 
                                     line=dict(color=theme['base_color'], dash=theme['dash'], width=2)), row=3, col=1)

            fig.update_layout(height=800, paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', margin=dict(l=10, r=10, t=50, b=10))
            fig.update_yaxes(showgrid=True, gridcolor='#222222', zeroline=True, zerolinecolor='#333333')
            st.plotly_chart(fig, use_container_width=True)



# --- TAB B: TRACK MAP ---
with tab2:
    st.header("Dominio de Pista (Track Map)")
    st.markdown("Comparación de Zonas de Frenada sobre Asfalto Calculado")
    
    col_mapa, col_herramientas = st.columns([3, 1])
    import numpy as np
    import pandas as pd
    import os
    import plotly.colors as pc
    import struct
    import csv
    
    with col_herramientas:
        st.subheader("Configuración del Mapa")
        
        if 'limits_dir' not in st.session_state:
            st.session_state.limits_dir = os.getcwd()
            
        # 1. Selector de Carpeta de CSVs
        if st.button("📁 Cambiar Carpeta Límites", use_container_width=True):
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            folder_path = filedialog.askdirectory(master=root, initialdir=st.session_state.limits_dir)
            if folder_path:
                st.session_state.limits_dir = folder_path
                st.rerun()
        st.caption(f"Leyendo de: {st.session_state.limits_dir}")
        
        # 2. Escáner de Circuito
        if st.button("🔍 Escanear Mod (.ai)", use_container_width=True, type="primary"):
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            
            initial_dir = r"C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\content\tracks"
            if not os.path.exists(initial_dir): initial_dir = "C:\\"
                
            folder_path = filedialog.askdirectory(master=root, initialdir=initial_dir, title="Selecciona la carpeta del circuito (ej: spa)")
            if folder_path:
                track_name = os.path.basename(folder_path)
                ai_path = os.path.join(folder_path, "ai", "fast_lane.ai")
                out_path = os.path.join(st.session_state.limits_dir, f"{track_name}_track_limits.csv")
                
                if not os.path.exists(ai_path):
                    st.error(f"❌ No se encontró fast_lane.ai en: {ai_path}")
                else:
                    try:
                        with open(ai_path, 'rb') as f:
                            header_data = f.read(16)
                            version, node_count, pad1, pad2 = struct.unpack('iiii', header_data)
                            node_format = '4fi'
                            node_size = struct.calcsize(node_format)
                            center_nodes = []
                            for i in range(node_count):
                                node_bytes = f.read(node_size)
                                if len(node_bytes) < node_size: break
                                data = struct.unpack(node_format, node_bytes)
                                center_nodes.append({'x': data[0], 'z': data[2]})
                                
                            track_limits = []
                            track_width_half = 8.5
                            num_nodes = len(center_nodes)
                            for i in range(num_nodes):
                                if i % 10 != 0 and i != num_nodes - 1: continue
                                curr = center_nodes[i]
                                next_idx = (i + 1) % num_nodes
                                nxt = center_nodes[next_idx]
                                dx, dz = nxt['x'] - curr['x'], nxt['z'] - curr['z']
                                length = np.sqrt(dx**2 + dz**2)
                                if length == 0: length = 1
                                dx /= length; dz /= length
                                norm_x, norm_z = -dz, dx
                                
                                track_limits.append({
                                    'inner_x': curr['x'] + norm_x * track_width_half, 'inner_z': curr['z'] + norm_z * track_width_half,
                                    'outer_x': curr['x'] - norm_x * track_width_half, 'outer_z': curr['z'] - norm_z * track_width_half
                                })
                            if track_limits: track_limits[-1] = track_limits[0].copy()
                            with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=['inner_x', 'inner_z', 'outer_x', 'outer_z'])
                                writer.writeheader()
                                writer.writerows(track_limits)
                        st.success(f"✅ {track_name} escaneado y registrado.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # 3. Selector Manual de Pista
        csv_files = [f for f in os.listdir(st.session_state.limits_dir) if f.endswith('_track_limits.csv')] if os.path.exists(st.session_state.limits_dir) else []
        opciones_limites = ["Automático (Metadata)", "Ninguno"] + csv_files
        selected_limit = st.selectbox("Forzar Trazado de Pista", opciones_limites)
        
        # 4. Leyenda Visual Dinámica
        legend_html = "<div style='background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-top: 15px;'>"
        legend_html += "<p style='margin-bottom: 5px;'><b>Leyenda del Mapa</b></p>"
        legend_html += "<div style='margin-bottom: 8px;'><span style='display:inline-block; width: 12px; height: 12px; background-color: #222222; border: 1px solid #AAAAAA; margin-right: 5px;'></span><b>Asfalto</b> (Límites)</div>"
        
        for lap in loaded_laps:
            coche_nombre = lap['theme']['name'] if 'name' in lap['theme'] else f"Coche {lap['id']}"
            color_freno = lap['theme']['brake_color']
            color_acel = lap['theme']['base_color']
            
            legend_html += f"<div style='margin-bottom: 4px; font-size: 0.9em;'>"
            legend_html += f"<b>{coche_nombre}:</b> <span style='color:{color_freno}'>■ Freno</span> | <span style='color:{color_acel}'>■ Acelerador</span>"
            legend_html += "</div>"
            
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

    with col_mapa:
        TRACK_ROTATION = st.session_state.track_rotation
        INVERT_X = st.session_state.invert_x
        INVERT_Z = st.session_state.invert_z
        
        fig_map = go.Figure()
        
        def transform_coords(x, z, angle_degrees, invert_x=False, invert_z=False):
            if invert_x: x = -x
            if invert_z: z = -z
            angle_rad = np.radians(angle_degrees)
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            x_rot = x * cos_a - z * sin_a
            z_rot = x * sin_a + z * cos_a
            return x_rot, z_rot
        
        def draw_gradient_heatmap(fig, df, colorscale, trace_prefix, line_width):
            if 'brake_pct_smooth' not in df.columns or 'throttle_pct_smooth' not in df.columns: return
            df = df.copy()
            df['pedal_index'] = (df['throttle_pct_smooth'] * 100) - (df['brake_pct_smooth'] * 100)
            bins = np.linspace(-100, 100, 21)
            df['bin'] = pd.cut(df['pedal_index'], bins=bins, labels=False, include_lowest=True)
            sampled_colors = pc.sample_colorscale(colorscale, np.linspace(0, 1, 20))
            df['color_hex'] = df['bin'].map(lambda b: sampled_colors[b] if not pd.isna(b) else sampled_colors[0])
            df['block_id'] = (df['color_hex'] != df['color_hex'].shift(1)).cumsum()
            for color, color_df in df.groupby('color_hex'):
                x_list, z_list = [], []
                for block_id, group in color_df.groupby('block_id'):
                    last_idx = group.index[-1]
                    next_idx = last_idx + 1
                    x_vals, z_vals = group['pos_x'].tolist(), group['pos_z'].tolist()
                    if next_idx in df.index:
                        x_vals.append(df.at[next_idx, 'pos_x'])
                        z_vals.append(df.at[next_idx, 'pos_z'])
                    x_list.extend(x_vals); x_list.append(np.nan)
                    z_list.extend(z_vals); z_list.append(np.nan)
                fig.add_trace(go.Scatter(x=x_list, y=z_list, mode='lines', line=dict(color=color, width=line_width), name=f"{trace_prefix} (Heatmap)", showlegend=False, hoverinfo='skip'))

        # Renderizado Selectivo de Asfalto
        target_csv = None
        if selected_limit != "Ninguno":
            if selected_limit == "Automático (Metadata)":
                track_name = loaded_laps[0]['metadata'].get('track', 'Desconocido') if loaded_laps else 'Desconocido'
                if track_name != "Desconocido":
                    target_csv = os.path.join(st.session_state.limits_dir, f'{track_name}_track_limits.csv')
                else:
                    st.info("Telemetría antigua sin metadatos de pista. Saltando dibujo de asfalto por defecto.")
            else:
                target_csv = os.path.join(st.session_state.limits_dir, selected_limit)

        if target_csv:
            try:
                tl_df = pd.read_csv(target_csv)
                tl_df['inner_x_trans'], tl_df['inner_z_trans'] = transform_coords(tl_df['inner_x'], tl_df['inner_z'], TRACK_ROTATION, INVERT_X, INVERT_Z)
                tl_df['outer_x_trans'], tl_df['outer_z_trans'] = transform_coords(tl_df['outer_x'], tl_df['outer_z'], TRACK_ROTATION, INVERT_X, INVERT_Z)
                fig_map.add_trace(go.Scatter(x=tl_df['inner_x_trans'], y=tl_df['inner_z_trans'], mode='lines', line=dict(color='#AAAAAA', width=2), name='Límite Interior', hoverinfo='skip'))
                fig_map.add_trace(go.Scatter(x=tl_df['outer_x_trans'], y=tl_df['outer_z_trans'], mode='lines', line=dict(color='#AAAAAA', width=2), fill='tonexty', fillcolor='#222222', name='Asfalto Vectorial', hoverinfo='skip'))
            except FileNotFoundError:
                if selected_limit == "Automático (Metadata)":
                    st.info(f"Modo Automático: No se encontró {os.path.basename(target_csv)}. Mostrando solo telemetría. Utiliza el Escáner para generarlo.")
                else:
                    st.error(f"El archivo {selected_limit} no existe.")
                    
        # Renderizado de Trazadas Vivas
        for i, lap in enumerate(loaded_laps):
            df_limpio = lap['dataframe'].copy()
            dist_jumps = np.sqrt(df_limpio['pos_x'].diff()**2 + df_limpio['pos_z'].diff()**2)
            df_limpio.loc[dist_jumps > 50, ['pos_x', 'pos_z']] = np.nan
            df_limpio['pos_x'], df_limpio['pos_z'] = transform_coords(df_limpio['pos_x'], df_limpio['pos_z'], TRACK_ROTATION, INVERT_X, INVERT_Z)
            width = 3 if i == 0 else 3 + (i * 1.5)
            draw_gradient_heatmap(fig_map, df_limpio, lap['theme']['gradient'], f"{lap['id']}", width)
                                                 
        fig_map.update_layout(
            dragmode='pan',
            yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            height=800, 
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            showlegend=True, 
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

# --- TAB C: CAR DYNAMICS ---
with tab3:
    st.header("Círculo de Tracción (G-Circle) y Suspensión")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("G-Force (Trail Braking / Traction)")
        fig_g = go.Figure()
        
        for lap in loaded_laps:
            df = lap['dataframe']
            theme = lap['theme']
            name = f"{lap['id']} - {lap['metadata']['time']}"
            
            # Filtramos para quitar paradas
            lap_g = df[df['speed_kmh'] > 10]
            fig_g.add_trace(go.Scatter(
                x=lap_g['accG_lat_smooth'], y=lap_g['accG_long_smooth'], 
                mode='markers',
                marker=dict(color=theme['base_color'], size=5, opacity=0.6),
                name=f"G-Force {name}"
            ))
            
        fig_g.update_layout(
            xaxis_title="Lateral G", yaxis_title="Longitudinal G (Accel/Brake)",
            yaxis=dict(scaleanchor="x", scaleratio=1), 
            height=600, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
        )
        st.plotly_chart(fig_g, use_container_width=True)
        
    with col2:
        st.subheader("Recorrido de Suspensión")
        fig_susp = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                                 subplot_titles=("Suspensión FL", "Suspensión FR", "Suspensión RL", "Suspensión RR"))
        
        corners = ['fl', 'fr', 'rl', 'rr']
        for i, corner in enumerate(corners):
            row = i + 1
            col_name = f'susp_travel_{corner}'
            for lap in loaded_laps:
                df = lap['dataframe']
                theme = lap['theme']
                name = f"{lap['id']} - {lap['metadata']['time']}"
                
                if col_name in df.columns:
                    fig_susp.add_trace(go.Scatter(
                        x=df['lap_distance'], y=df[col_name],
                        name=f'Susp {corner.upper()} {name}',
                        line=dict(color=theme['base_color'], dash=theme['dash'], width=2)
                    ), row=row, col=1)
                    
        fig_susp.update_layout(
            height=300 * 4,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_susp, use_container_width=True)

# --- TAB D: TYRES & BRAKES ---
with tab4:
    st.header("Dinámica de Neumáticos y Frenos")
    
    corners = ['fl', 'fr', 'rl', 'rr']
    
    st.subheader("Temperaturas de Neumáticos (Core Temp)")
    fig_tyres = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                              subplot_titles=("Front Left", "Front Right", "Rear Left", "Rear Right"))
    
    for i, corner in enumerate(corners):
        row = i + 1
        middle = f'tyre_temp_middle_{corner}'
        
        for lap in loaded_laps:
            df = lap['dataframe']
            theme = lap['theme']
            name = f"{lap['id']} - {lap['metadata']['time']}"
            
            if middle in df.columns:
                fig_tyres.add_trace(go.Scatter(
                    x=df['lap_distance'], y=df[middle], 
                    name=f'{corner.upper()} {name}',
                    line=dict(color=theme['base_color'], dash=theme['dash'], width=2)
                ), row=row, col=1)
                
    fig_tyres.update_layout(
        height=300 * 4,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_tyres, use_container_width=True)
    
    st.subheader("Temperaturas de Frenos")
    fig_brakes = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                               subplot_titles=("Frenos FL", "Frenos FR", "Frenos RL", "Frenos RR"))
    
    for i, corner in enumerate(corners):
        row = i + 1
        b_temp = f'brake_temp_{corner}'
        
        for lap in loaded_laps:
            df = lap['dataframe']
            theme = lap['theme']
            name = f"{lap['id']} - {lap['metadata']['time']}"
            
            if b_temp in df.columns:
                fig_brakes.add_trace(go.Scatter(
                    x=df['lap_distance'], y=df[b_temp], 
                    name=f'Brake {corner.upper()} {name}',
                    line=dict(color=theme['brake_color'], dash=theme['dash'], width=2)
                ), row=row, col=1)
                
    fig_brakes.update_layout(
        height=300 * 4,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_brakes, use_container_width=True)


# --- TAB E: AI COACH ---
with tab5:
    st.header("🤖 Asistente de Pilotaje IA (Debrief)")
    
    if len(loaded_laps) < 2:
        st.warning("⚠️ El AI Coach requiere al menos 2 vueltas cargadas para generar comparativas.")
    else:
        st.markdown("Algoritmo de **Nearest Neighbors (KDTree)** interpolado espacialmente para el cálculo de Deltas de Velocidad a lo largo del circuito.")
        
        from scipy.spatial import cKDTree
        import numpy as np
        
        ref_lap = loaded_laps[0]
        ref_df = ref_lap['dataframe']
        
        # 1. Construir el árbol espacial usando las coordenadas de la Vuelta Base
        tree = cKDTree(ref_df[['pos_x', 'pos_z']].values)
        
        # 2. Iterar sobre las vueltas restantes
        for lap in loaded_laps[1:]:
            comp_df = lap['dataframe']
            coche_nombre = lap['theme']['name'] if 'name' in lap['theme'] else f"Coche {lap['id']}"
            
            st.divider()
            st.subheader(f"📊 Análisis: {ref_lap['theme']['name']} vs {coche_nombre}")
            
            # --- Layout Ejecutivo: Diferencia de Tiempo Global ---
            def parse_time(t_str):
                parts = t_str.replace('.', ':').split(':')
                if len(parts) >= 3:
                    return int(parts[0])*60000 + int(parts[1])*1000 + int(parts[2])
                return 0
                
            ref_time_ms = parse_time(ref_lap['metadata']['time'])
            comp_time_ms = parse_time(lap['metadata']['time'])
            
            delta_ms = comp_time_ms - ref_time_ms
            delta_str = f"{delta_ms/1000.0:+.3f}s"
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Tiempo Referencia (Base)", ref_lap['metadata']['time'])
            col2.metric(f"Tiempo {coche_nombre}", lap['metadata']['time'])
            col3.metric("Delta Global", delta_str, delta_color="inverse")
            
            # --- Cálculo de Deltas Dinámico Espacial ---
            distances, ref_indices = tree.query(comp_df[['pos_x', 'pos_z']].values)
            
            # delta_v: Velocidad del Comparado - Velocidad del Base en el punto espacial más cercano
            delta_v = comp_df['speed_kmh'].values - ref_df['speed_kmh'].iloc[ref_indices].values
            
            # --- El Veredicto (Texto) ---
            min_delta_idx = np.argmin(delta_v)
            worst_loss_v = delta_v[min_delta_idx]
            worst_dist = comp_df['lap_distance'].iloc[min_delta_idx]
            
            comp_speed_at_worst = comp_df['speed_kmh'].iloc[min_delta_idx]
            ref_speed_at_worst = ref_df['speed_kmh'].iloc[ref_indices[min_delta_idx]]
            
            if worst_loss_v < -5.0:
                st.error(f"⚠️ **{coche_nombre}**: La mayor pérdida de tiempo se detectó alrededor del metro **{worst_dist:.0f}** de la pista. Velocidad **{comp_speed_at_worst:.0f} km/h** vs **{ref_speed_at_worst:.0f} km/h** de la referencia.")
            else:
                st.success(f"✅ **{coche_nombre}**: No se detectaron pérdidas graves de velocidad respecto a la referencia (Mayor Delta Negativo: {worst_loss_v:.1f} km/h).")
                
            # --- Gráfico de Delta V ---
            pos_delta = np.where(delta_v >= 0, delta_v, 0)
            neg_delta = np.where(delta_v < 0, delta_v, 0)
            
            fig_delta = go.Figure()
            
            # Delta Positivo (Ganancia) -> Verde
            fig_delta.add_trace(go.Scatter(
                x=comp_df['lap_distance'], y=pos_delta, mode='lines',
                line=dict(color='#32CD32', width=0), fill='tozeroy', fillcolor='rgba(50, 205, 50, 0.5)',
                name="Ganancia vs Base"
            ))
            
            # Delta Negativo (Pérdida) -> Rojo
            fig_delta.add_trace(go.Scatter(
                x=comp_df['lap_distance'], y=neg_delta, mode='lines',
                line=dict(color='#FF4B4B', width=0), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.5)',
                name="Pérdida vs Base"
            ))
            
            fig_delta.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
            
            fig_delta.update_layout(
                xaxis_title="Distancia de Vuelta (m)",
                yaxis_title="Delta Velocidad (km/h)",
                height=350,
                paper_bgcolor='#0E1117',
                plot_bgcolor='#0E1117',
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_delta, use_container_width=True)
            
            # --- Tabla de Análisis Detallado (Restauración) ---
            st.divider()
            st.subheader(f"📑 Análisis de Ápices: {coche_nombre}")
            
            from scipy.signal import find_peaks
            
            # Identificar Ápices en Ref (Baja velocidad)
            peaks, _ = find_peaks(-ref_df['speed_kmh'], distance=100) 
            apex_data = []
            
            # Árbol temporal para buscar el punto equivalente del comparado al ápice de la base
            comp_tree = cKDTree(comp_df[['pos_x', 'pos_z']].values)
            
            for p in peaks:
                idx = ref_df.index[p]
                r_pt = ref_df.loc[idx]
                
                lat_g = abs(r_pt.get('accG_lat_smooth', 0))
                steer = abs(r_pt.get('steer_angle_smooth', 0))
                if steer < 0.3 and lat_g < 0.5:
                    continue
                    
                # Buscar espacialmente en la vuelta comparada
                dist_m, comp_idx_iloc = comp_tree.query([r_pt['pos_x'], r_pt['pos_z']])
                c_pt = comp_df.iloc[comp_idx_iloc]
                
                # Producto Vectorial (Cut vs Wide)
                p_prev = max(0, p - 5)
                p_next = min(len(ref_df)-1, p + 5)
                
                idx_next = ref_df.index[p_next]
                idx_prev = ref_df.index[p_prev]
                
                vx = ref_df.loc[idx_next]['pos_x'] - ref_df.loc[idx_prev]['pos_x']
                vz = ref_df.loc[idx_next]['pos_z'] - ref_df.loc[idx_prev]['pos_z']
                
                ex = c_pt['pos_x'] - r_pt['pos_x']
                ez = c_pt['pos_z'] - r_pt['pos_z']
                
                cross_prod = (vx * ez) - (vz * ex)
                is_right_corner = r_pt.get('accG_lat_smooth', 0) > 0 
                
                direction = "Dentro (Cut)"
                if is_right_corner:
                    if cross_prod > 0: direction = "Fuera (Wide)"
                else:
                    if cross_prod < 0: direction = "Fuera (Wide)"
                    
                # Deltas en el ápice
                speed_delta_p = c_pt['speed_kmh'] - r_pt['speed_kmh']
                steer_delta_p = c_pt.get('steer_angle_smooth', 0) - r_pt.get('steer_angle_smooth', 0)
                
                apex_data.append({
                    "Distancia (m)": f"{r_pt['lap_distance']:.0f}m",
                    "Curva (Sector)": f"Apex a {r_pt.get('lap_pct', 0):.1f}%",
                    "OFFSET Δ (m)": f"{dist_m:.2f}m [{direction}]",
                    "PERDIDA DE VEL.": f"{speed_delta_p:+.1f} km/h",
                    "CORRECCIÓN VOLANTE (Δ)": f"{steer_delta_p:+.1f}°",
                    "Ref Speed": f"{r_pt['speed_kmh']:.0f} km/h"
                })
                
            if len(apex_data) > 0:
                df_coach = pd.DataFrame(apex_data)
                st.dataframe(df_coach, use_container_width=True)
                
                # Botón de exportación adaptado
                csv_data = df_coach.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Exportar Matriz {coche_nombre} (CSV)",
                    data=csv_data,
                    file_name=f"Coach_Analysis_{coche_nombre}.csv",
                    mime="text/csv",
                    key=f"export_{lap['id']}"
                )
            else:
                st.info("No se detectaron curvas válidas con la sensibilidad actual.")

# --- TAB F: CONFIGURACIÓN ---
with tab6:
    st.header("Panel de Control del Ingeniero")
    st.subheader("🎨 Personalización Visual")
    
    # Transformación Geométrica
    st.markdown("**Geometría de Pista**")
    st.session_state.track_rotation = st.slider("Rotación de Pista (Grados)", -180, 180, st.session_state.track_rotation)
    col_x, col_z = st.columns(2)
    with col_x:
        st.session_state.invert_x = st.checkbox("Invertir Eje X", st.session_state.invert_x)
    with col_z:
        st.session_state.invert_z = st.checkbox("Invertir Eje Z", st.session_state.invert_z)
        
    # Theming Dinámico
    st.markdown("**Colores por Vuelta**")
    for i in range(3):
        with st.expander(f"Personalizar {st.session_state.themes[i]['name']}"):
            c1, c2 = st.columns(2)
            with c1:
                new_base = st.color_picker("Acelerador / Base", st.session_state.themes[i]['base_color'], key=f"base_color_{i}")
                st.session_state.themes[i]['base_color'] = new_base
            with c2:
                new_brake = st.color_picker("Freno", st.session_state.themes[i]['brake_color'], key=f"brake_color_{i}")
                st.session_state.themes[i]['brake_color'] = new_brake

# --- TAB G: CAPTURA EN VIVO ---
with tab7:
    st.title("🔴 Captura en Vivo (Assetto Corsa)")
    
    st.markdown("### Directorio de Guardado")
    
    col_btn, col_path = st.columns([1, 4])
    with col_btn:
        if st.button("📁 Cambiar Carpeta", use_container_width=True):
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1) # Fuerza la ventana al frente
            folder_path = filedialog.askdirectory(master=root, initialdir=st.session_state.save_dir)
            if folder_path:
                st.session_state.save_dir = folder_path
                st.rerun()
                
    with col_path:
        st.code(st.session_state.save_dir, language='plaintext')

    st.divider()

    # Jerarquía visual del Estado
    st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
    if st.session_state.is_recording:
        st.markdown("<h1 style='color: #FF4B4B;'>🔴 GRABANDO</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='color: #888888;'>⚪ STANDBY</h1>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botones Primarios
    col_dummy1, col_start, col_stop, col_dummy2 = st.columns([1, 2, 2, 1])
    
    with col_start:
        if st.button("▶️ Iniciar Captura", type="primary", use_container_width=True, disabled=st.session_state.is_recording):
            env = os.environ.copy()
            env['AC_SAVE_DIR'] = st.session_state.save_dir
            env['PYTHONIOENCODING'] = 'utf-8'
            
            log_file = open('recorder_log.txt', 'a', encoding='utf-8')
            proc = subprocess.Popen(['python', 'record_session.py'], env=env, stdout=log_file, stderr=subprocess.STDOUT)
            st.session_state.recorder_process = proc
            st.session_state.is_recording = True
            st.rerun()
            
    with col_stop:
        if st.button("⏹️ Detener Captura", type="primary", use_container_width=True, disabled=not st.session_state.is_recording):
            if st.session_state.recorder_process:
                st.session_state.recorder_process.terminate()
                st.session_state.recorder_process = None
            st.session_state.is_recording = False
            st.rerun()


