import struct
import csv
import sys
import numpy as np

ai_path = r'H:\SteamLibrary\steamapps\common\assettocorsa\content\tracks\fn_bahrain\f1\ai\fast_lane.ai'
out_path = r'c:\Users\Mati\Desktop\PROGRAMACION\FACTORYSETUP_ASSETO_CORSA\bahrain_track_limits.csv'

try:
    with open(ai_path, 'rb') as f:
        # Read header (16 bytes)
        # 4 bytes unknown (version?), 4 bytes node count, 8 bytes padding
        header_data = f.read(16)
        version, node_count, pad1, pad2 = struct.unpack('iiii', header_data)
        
        print(f"Nodes declared in header: {node_count}")
        
        # El patrón descubierto es de 20 bytes: 4 floats + 1 int
        node_format = '4fi'
        node_size = struct.calcsize(node_format)
        
        center_nodes = []
        
        for i in range(node_count):
            node_bytes = f.read(node_size)
            if len(node_bytes) < node_size:
                print(f"EOF reached prematurely at node {i}")
                break
                
            data = struct.unpack(node_format, node_bytes)
            center_nodes.append({'x': data[0], 'z': data[2]})
            
        # Geometría Procedural: Calcular vectores normales y proyectar bordes
        track_limits = []
        track_width_half = 8.5 # 17 metros de ancho total para mejorar visibilidad
        
        
        num_nodes = len(center_nodes)
        for i in range(num_nodes):
            # Downsampling: Procesar 1 de cada 10, y siempre el último
            if i % 10 != 0 and i != num_nodes - 1:
                continue
                
            curr = center_nodes[i]
            # Tomar el siguiente nodo para calcular la tangente (looping al inicio si es el final)
            next_idx = (i + 1) % num_nodes
            nxt = center_nodes[next_idx]
            
            dx = nxt['x'] - curr['x']
            dz = nxt['z'] - curr['z']
            
            # Normalizar el vector tangente
            length = np.sqrt(dx**2 + dz**2)
            if length == 0:
                length = 1
            dx /= length
            dz /= length
            
            # Vector Normal perpendicular (girar 90 grados: -dz, dx)
            # En coordenadas top-down (X, Z), si giramos 90 grados a la izquierda: (-dz, dx)
            norm_x = -dz
            norm_z = dx
            
            # Proyectar límites
            inner_x = curr['x'] + norm_x * track_width_half
            inner_z = curr['z'] + norm_z * track_width_half
            
            outer_x = curr['x'] - norm_x * track_width_half
            outer_z = curr['z'] - norm_z * track_width_half
            
            track_limits.append({
                'inner_x': inner_x, 'inner_z': inner_z,
                'outer_x': outer_x, 'outer_z': outer_z
            })
            
        # LOOP CLOSURE: Asegurar que el último nodo sea exactamente igual al primero
        if track_limits:
            track_limits[-1] = track_limits[0].copy()
            
        # Export to CSV
        with open(out_path, 'w', newline='') as csvfile:
            fieldnames = ['inner_x', 'inner_z', 'outer_x', 'outer_z']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in track_limits:
                writer.writerow(row)
                
        print(f"SUCCESS: Extracted {len(track_limits)} nodes and saved to {out_path}")
        
except Exception as e:
    print(f"ERROR: Fallo crítico. Detalle: {e}")
    print("--- HEX DUMP DE LOS PRIMEROS 100 BYTES ---")
    try:
        with open(ai_path, 'rb') as f:
            f.seek(0)
            dump = f.read(100)
            print(" ".join([f"{b:02x}" for b in dump]))
    except Exception as e2:
        print(f"No se pudo generar el hex dump: {e2}")
    sys.exit(1)
