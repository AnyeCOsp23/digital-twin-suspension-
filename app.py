import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import sys
import os
import json
import streamlit.components.v1 as components
import numpy as np
import base64

sys.path.append(os.path.dirname(__file__))

try:
    from backend.physics import SuspensionDigitalTwin
    from backend.alert_system import check_maintenance_alert, export_peaks_json
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.stop()

st.set_page_config(page_title="Gemelo Digital 3D", layout="wide", page_icon="🏎️")
st.markdown('''<style>
.main { background-color: #0e1117; }
.stMetric { background: rgba(0, 255, 136, 0.1); border-radius: 10px; padding: 15px; border-left: 5px solid #00ff88; }
</style>''', unsafe_allow_html=True)

st.title("🏎️ Gemelo Digital 3D: Sistema masa-resorte-amortiguador")

# ===== PANEL DE CONTROL =====
st.sidebar.markdown("### ⚙️ Configuración de Suspensión")

modo_amortiguacion = st.sidebar.radio(
    "Modo de Sistema",
    ["Manual", "Subamortiguado", "Críticamente amortiguado", "Sobreamortiguado", "Roto (Colapso)"]
)

if modo_amortiguacion == "Manual":
    m = st.sidebar.slider("Masa del chasis (kg)", 0.5, 10.0, 2.0, step=0.1)
    k = st.sidebar.slider("Constante del resorte k (N/m)", 1.0, 100.0, 50.0, step=0.5)
    b = st.sidebar.slider("Coef. de amortiguamiento b (Ns/m)", 0.1, 100.0, 4.0, step=0.5)
elif modo_amortiguacion == "Subamortiguado":
    m, k, b = 2.0, 50.0, 1.8  # b más bajo para más oscilación
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")
elif modo_amortiguacion == "Críticamente amortiguado":
    m, k, b = 2.0, 50.0, 20.0
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")
elif modo_amortiguacion == "Sobreamortiguado":
    m, k, b = 2.0, 10.0, 80.0
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")
else: # Roto (Colapso)
    m, k, b = 10.0, 1.0, 0.1
    st.sidebar.warning(f"**Valores críticos 💥:**\nEl modelo carece de fuerza de resortes para resistir. Se romperá tras el 1er o 2do bache.")

st.sidebar.markdown("---")

modo_baches = st.sidebar.radio(
    "Generación de Baches",
    ["Aleatorios (Infinita)", "Cantidad Exacta"]
)
if modo_baches == "Cantidad Exacta":
    exact_baches = st.sidebar.number_input("Número de Baches", min_value=0, max_value=50, value=3, step=1)
else:
    exact_baches = None

st.sidebar.markdown("---")
mute_alarm = st.sidebar.checkbox("🔕 Silenciar Alarma", value=False, help="Activa para silenciar los sonidos del sistema.")
st.sidebar.markdown("---")

# ===== SIMULACIÓN =====
if 'sim_params' not in st.session_state or st.session_state.sim_params != (m, b, k, exact_baches):
    st.session_state.sim_params = (m, b, k, exact_baches)
    twin = SuspensionDigitalTwin(m, b, k)
    t, x, v = twin.simulate(t_span=(0, 20.0), n_points=800, exact_num_bumps=exact_baches)
    st.session_state.twin_cached = (twin, t, x, v)
    st.session_state.start_time_sync = int(time.time() * 1000) + 150
else:
    twin, t, x, v = st.session_state.twin_cached

info = twin.get_system_info()

# ===== EXPORTACIÓN (SIDEBAR) =====
st.sidebar.markdown("### 💾 Exportar Datos")

export_peaks_json(t, x, m, b, k, "picos_vibracion.json")
try:
    with open("picos_vibracion.json", "r", encoding="utf-8") as f:
        json_data = f.read()
except FileNotFoundError:
    json_data = "{}"

df_export = pd.DataFrame({
    'Tiempo (s)': t,
    'Desplazamiento (m)': x,
    'Velocidad (m/s)': v
})
csv_data = df_export.to_csv(index=False, encoding='utf-8')

st.sidebar.download_button(
    label="⬇️ Descargar Picos JSON",
    data=json_data,
    file_name="picos_vibracion.json",
    mime="application/json",
    help="Descarga los picos reales de vibración detectados en la simulación."
)

st.sidebar.download_button(
    label="📊 Descargar Trayectoria CSV",
    data=csv_data,
    file_name="simulacion_suspension.csv",
    mime="text/csv",
    help="Descarga todos los puntos de la simulación (t, x, v)."
)

st.sidebar.info(f"📊 Total de puntos: {len(t)} | Duración: {t[-1]:.2f}s")

# ===== MÉTRICAS PRINCIPALES =====
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Frecuencia natural (ωn)", f"{info['wn']} rad/s", help="Frecuencia natural del sistema no amortiguado")

with col2:
    st.metric("Razón de amortiguamiento (ζ)", f"{info['zeta']}", help="Coeficiente de amortiguamiento relativo")

with col3:
    is_broken = "ROTO" in info['status']
    is_overdamped = "Sobreamortiguado" in info['status']
    is_underdamped = "Subamortiguado" in info['status']
    
    alert, stab_time = check_maintenance_alert(m, b, k)
    
    critical_alert = alert
    warning_alert = False # Ya no se usa, todo alert > 3s es critico
    
    if is_broken:
        critical_alert = True
        color_stab = "💥"
        st.metric(f"{color_stab} Tiempo de estabilización", "INF (ROTO)", help="El amortiguador se ha dañado severamente")
    else:
        if critical_alert:
            color_stab = "🔴"
        else:
            color_stab = "🟢"
        st.metric(f"{color_stab} Tiempo de estabilización", f"{stab_time}s", help="Tiempo aprox. de establización al equilibrio")

with col4:
    desv = float(np.max(np.abs(x)))
    val_disp = f"0.33m (Roto)" if is_broken else f"{desv:.3f}m"
    st.metric("Desv. máxima", val_disp, help="Desplazamiento máximo registrado")

st.markdown("---")

# Inicializar session state para rastrear cambios de estado
if 'prev_alert_state' not in st.session_state:
    st.session_state.prev_alert_state = critical_alert

# Detectar cambio de estado (de óptimo a alerta o viceversa)
state_changed = st.session_state.prev_alert_state != critical_alert
st.session_state.prev_alert_state = critical_alert

# Placeholder para el sonido que se mantiene
sound_placeholder = st.empty()

if critical_alert and not mute_alarm:
    # Reproducir sonido de alerta CONTINUAMENTE sin pausas
    with sound_placeholder.container():
        st.components.v1.html("""
        <script>
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let isAlertPlaying = true;
            
            function playAlertSoundContinuous() {
                if (!isAlertPlaying) return;
                
                // Sonido de alerta: 5 tonos continuos sin pausa
                for (let rep = 0; rep < 5; rep++) {
                    const osc = audioContext.createOscillator();
                    const gain = audioContext.createGain();
                    osc.connect(gain);
                    gain.connect(audioContext.destination);
                    
                    osc.frequency.value = 800; // Frecuencia fija
                    osc.type = 'sine';
                    
                    // Volumen incremental DUPLICADO: 0.4, 0.6, 0.8, 1.0, 1.0 (máximo)
                    const volume = Math.min(1.0, 0.4 + (rep * 0.2));
                    
                    // Timing: cada repetición dura 0.25s SIN PAUSA
                    const startTime = audioContext.currentTime + (rep * 0.25);
                    
                    gain.gain.setValueAtTime(volume, startTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.25);
                    osc.start(startTime);
                    osc.stop(startTime + 0.25);
                }
                
                // Repetir después de 1.25s (5 * 0.25s)
                setTimeout(playAlertSoundContinuous, 1250);
            }
            
            // Iniciar sonido de alerta
            playAlertSoundContinuous();
            
            // Detener cuando Streamlit rerandea (cambia de estado)
            window.addEventListener('beforeunload', () => {
                isAlertPlaying = false;
            });
        </script>
        """, height=0)
elif not critical_alert and not warning_alert and not mute_alarm:
    # Reproducir sonido de éxito SOLO cuando cambia de alerta a óptimo
    if state_changed:
        with sound_placeholder.container():
            st.components.v1.html("""
            <script>
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const notes = [523.25, 659.25, 783.99, 987.77, 1046.50]; // Do, Mi, Sol, Si, Do agudo
                
                // 5 notas con volumen incremental (SIN REPETICIÓN)
                notes.forEach((freq, i) => {
                    const osc = audioContext.createOscillator();
                    const gain = audioContext.createGain();
                    osc.connect(gain);
                    gain.connect(audioContext.destination);
                    
                    osc.frequency.value = freq;
                    osc.type = 'sine';
                    
                    // Volumen incremental: 0.1, 0.2, 0.3, 0.4, 0.5
                    const volume = 0.1 + (i * 0.1);
                    
                    // Timing: cada nota dura 0.3s
                    const startTime = audioContext.currentTime + (i * 0.35);
                    
                    gain.gain.setValueAtTime(volume, startTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);
                    osc.start(startTime);
                    osc.stop(startTime + 0.3);
                });
            </script>
            """, height=0)

st.markdown("---")

# ===== LAYOUT PRINCIPAL: 3D + GRÁFICAS =====
col_3d, col_graph = st.columns([1.5, 1])

# ============ VISOR 3D ============
with col_3d:
    st.subheader("🎮 Visor Industrial del Gemelo Digital 3D")
    try:
        base_dir = os.path.dirname(__file__)
        comp_path = os.path.join(base_dir, "frontend", "component.html")
        
        if not os.path.exists(comp_path):
            st.warning(f"⚠️ Componente no encontrado en: {comp_path}")
            st.info("Usando visor 3D embebido...")
            # Si no existe, usar visor mínimo embebido
            raise FileNotFoundError(f"No encontrado: {comp_path}")
        
        with open(comp_path, "r", encoding="utf-8") as f:
            html_3d = f.read()
        
        # Preparar GLB del carro (opcional)
        car_glb_b64 = ""
        try:
            car_path = os.path.join(os.path.dirname(__file__), "assets", "car.glb")
            if os.path.exists(car_path):
                with open(car_path, "rb") as bf:
                    car_glb_b64 = base64.b64encode(bf.read()).decode("utf-8")
        except Exception:
            pass

        # Inyectar datos de forma segura
        start_time_sync = st.session_state.start_time_sync
        
        traj_json = json.dumps([float(v) for v in x.tolist()], ensure_ascii=False)
        time_json = json.dumps([float(v) for v in t.tolist()], ensure_ascii=False)
        vel_json = json.dumps([float(v) for v in v.tolist()], ensure_ascii=False)
        params_json = json.dumps({
            "m": float(m),
            "k": float(k),
            "b": float(b)
        }, ensure_ascii=False)
        bumps_list = getattr(twin, 'random_bumps', [])
        bumps_formatted = [{"s": b[0], "e": b[1]} for b in bumps_list]
        bumps_json = json.dumps(bumps_formatted, ensure_ascii=False)
        
        # Reemplazos robustos
        html_3d = html_3d.replace('__TRAJECTORY_DATA__', traj_json)
        html_3d = html_3d.replace('__TIME_DATA__', time_json)
        html_3d = html_3d.replace('__VELOCITY_DATA__', vel_json)
        html_3d = html_3d.replace('__SIM_PARAMS__', params_json)
        html_3d = html_3d.replace('__BUMPS_DATA__', bumps_json)
        html_3d = html_3d.replace('__START_SYNC_MS__', str(start_time_sync))
        html_3d = html_3d.replace('__CAR_MODEL_B64__', car_glb_b64)
        
        components.html(html_3d, height=650, scrolling=False)
        
    except Exception as e:
        st.error(f"❌ Error cargando componente 3D: {e}")

# ============ GRÁFICAS EN VIVO ============
with col_graph:
    st.subheader("📊 Simulación de Suspensión")
    
    if is_broken:
        alert_bg = 'rgba(51, 0, 0, 0.8)'
        alert_color = '#ff3366'
        alert_msg = f"💥 COLAPSO ESTRUCTURAL: Amortiguador Roto"
        blink_css = ".alert-banner { animation: blinker 0.6s cubic-bezier(1, 0, 0, 1) infinite; color: #fff; text-shadow: 0 0 5px #ff3366; } @keyframes blinker { 50% { opacity: 0; } }"
    elif critical_alert:
        alert_bg = 'rgba(51, 0, 0, 0.8)'
        alert_color = '#ff3366'
        alert_msg = f"ERROR: Amortiguador desgastado. Requiere mantenimiento. ({stab_time}s)"
        blink_css = ".alert-banner { animation: blinker 0.6s cubic-bezier(1, 0, 0, 1) infinite; color: #fff; text-shadow: 0 0 5px #ff3366; } @keyframes blinker { 50% { opacity: 0.5; } }"
    else:
        alert_bg = 'rgba(0, 51, 26, 0.8)'
        alert_color = '#00ff88'
        alert_msg = f"✅ ESTADO OPTIMO: {stab_time}s (dentro de límite)"
        blink_css = ""
    
    plot_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background-color: #111111; font-family: monospace; overflow: hidden; }}
            #plot {{ width: 100%; height: calc(100vh - 80px); background: #0a0e1a; }}
            #legend {{
                position: absolute; top: 10px; right: 10px; color: #00ff88;
                background: rgba(0, 0, 0, 0.8); padding: 8px 12px; border-radius: 5px;
                font-size: 11px; z-index: 10;
            }}
            .alert-banner {{
                position: absolute; bottom: 0; width: 100%; height: 80px;
                display: flex; align-items: center; justify-content: center;
                text-align: center;
                font-family: Arial, sans-serif; font-size: 20px; font-weight: bold;
                background-color: {alert_bg};
                color: {alert_color};
                border-top: 1px solid {alert_color};
                box-shadow: 0 0 10px {alert_color};
            }}
            {blink_css}
        </style>
    </head>
    <body style="height: 100vh;">
        <div id="plot"></div>
        <div class="alert-banner">
            {alert_msg}
        </div>
        <div id="legend">
            <div>Desplazamiento x(t)</div>
            <div style="color: #ff6b35; font-size: 10px; margin-top: 3px;">Eje Y: metros</div>
        </div>
        <script>
            // --- MOTOR DE FÍSICA EN TIEMPO REAL JAVASCRIPT ---
            // Le pasamos todo un arsenal de 3600 segundos de baches generados por Python
            // Y ambas partes (3D y Gráfica) simulan numéricamente a la vez, haciéndolo 100% INFINITO.
            const BUMPS = {bumps_json};
            const m = {m}, k = {k}, b = {b};
            const globalStart = {st.session_state.start_time_sync};
            
            // Inicializar simulación continua
            let sim_x = 0, sim_v = 0, sim_t = 0;
            const sim_dt = 0.005;
            let bumpIdx = 0;
            let is_broken = false; // Empezar siempre sano, se romperá solo cuando x > 0.4
            
            function stepPhysicsTo(targetT) {{
                while(sim_t < targetT) {{
                    if (is_broken) {{
                        sim_v += 9.81 * sim_dt; // Gravedad comprime hacia 0.33
                        sim_x += sim_v * sim_dt;
                        if (sim_x > 0.33) {{
                            sim_x = 0.33;
                            sim_v = 0.0;
                        }}
                        sim_t += sim_dt;
                        continue;
                    }}

                    let force = 0;
                    while(bumpIdx < BUMPS.length && BUMPS[bumpIdx].e < sim_t) bumpIdx++;
                    if (bumpIdx < BUMPS.length && sim_t >= BUMPS[bumpIdx].s && sim_t <= BUMPS[bumpIdx].e) {{
                        force = 50.0 * 0.15; // Fuerza reducida
                    }}
                    let acc = (force - b * sim_v - k * sim_x) / m;
                    sim_v += acc * sim_dt;
                    sim_x += sim_v * sim_dt;

                    // Detección de ruptura local
                    if (Math.abs(sim_x) > 0.4) {{
                        is_broken = true;
                    }}

                    // Topes físicos
                    if (sim_x > 0.45) {{ sim_x = 0.45; sim_v *= -0.2; }}
                    if (sim_x < -0.45) {{ sim_x = -0.45; sim_v *= -0.2; }}

                    sim_t += sim_dt;
                }}
                return sim_x;
            }}

            const WINDOW_SEC = 3.0; // segundos en pantalla
            const FPS_GRAFICA = 50; // frames por segundo de telemetría visible
            const WINDOW_POINTS = WINDOW_SEC * FPS_GRAFICA;
            const dt_vis = 1.0 / FPS_GRAFICA;
            
            let xData = Array.from({{length: WINDOW_POINTS}}, (_, i) => i * dt_vis);
            let yData = Array(WINDOW_POINTS).fill(0);
            let next_sample_t = 0;
            
            const layoutConfig = {{
                template: 'plotly_dark',
                paper_bgcolor: '#0a0e1a',
                plot_bgcolor: '#0a0e1a',
                margin: {{l: 35, r: 15, t: 15, b: 30}},
                xaxis: {{
                    title: 'Tiempo (s)',
                    showgrid: true,
                    gridcolor: '#333333',
                    zeroline: false,
                    fixedrange: true
                }},
                yaxis: {{
                    title: 'Desplazamiento (m)',
                    showgrid: true,
                    gridcolor: '#333333',
                    zeroline: true,
                    zerolinecolor: '#ff3366',
                    zerolinewidth: 2,
                    fixedrange: true,
                    range: [-0.4, 0.4] // Eje Y estanco, no hace zoom a micrometros aleatorios
                }},
                font: {{ size: 11, color: '#00ff88' }},
                showlegend: false,
                hovermode: 'x unified'
            }};

            // Fast-forward (si el componente acaba de cargar, simular hasta el presente rapidísimo)
            let initialNow = Math.max(0, (Date.now() - globalStart) / 1000);
            while(next_sample_t <= initialNow) {{
                stepPhysicsTo(next_sample_t);
                xData.push(next_sample_t);
                xData.shift();
                yData.push(sim_x);
                yData.shift();
                next_sample_t += dt_vis;
            }}

            Plotly.newPlot('plot', 
                [{{ x: xData, y: yData, mode: 'lines',
                   line: {{color: '#00E5FF', width: 3}},
                   fill: 'tozeroy',
                   fillcolor: 'rgba(0, 229, 255, 0.1)',
                   hovertemplate: '<b>t:</b> %{{x:.2f}}s<br><b>y:</b> %{{y:.4f}}m<extra></extra>'
                }}],
                layoutConfig,
                {{responsive: true, displayModeBar: false}});
            
            // Streaming sin reinicios, simulado numéricamente a reloj mundial (100% libre de saltos de tiempo)
            setInterval(() => {{
                let nowT = Math.max(0, (Date.now() - globalStart) / 1000);
                let updated = false;
                
                while(next_sample_t <= nowT) {{
                    stepPhysicsTo(next_sample_t);
                    xData.push(next_sample_t);
                    xData.shift();
                    yData.push(sim_x);
                    yData.shift();
                    next_sample_t += dt_vis;
                    updated = true;
                }}
                
                if (updated) {{
                    let minX = xData[0];
                    let maxX = xData[xData.length - 1];
                    Plotly.update('plot', {{x: [xData], y: [yData]}}, {{'xaxis.range': [minX, maxX]}});
                }}
            }}, 20); // Fluidez máxima nativa
        </script>
    </body>
    </html>
    """
    components.html(plot_html, height=550, scrolling=False)
    
    # Nuevo componente UI: Tipo de Amortiguamiento
    if is_broken:
        status_text = "AMORTIGUADOR ROTO 💥"
        color_rgb = "255, 51, 102" # Rojo
    elif not critical_alert:  # Tarda <= 3.0s
        status_text = "CRITICAMENTE AMORTIGUADO 🟢 (Respuesta ideal)"
        color_rgb = "0, 255, 136" # Verde brillante
    else:
        status_text = info['status'] + " 🔴"
        color_rgb = "255, 51, 102" # Rojo para error por > 3s

    damping_card_html = f"""
    <div style="background-color: rgba({color_rgb}, 0.15); border-radius: 10px; padding: 15px; border-left: 5px solid rgb({color_rgb}); margin-top: 20px; font-family: 'IBM Plex Sans', sans-serif;">
        <div style="font-size: 14px; color: #a6a6a6; display: flex; align-items: center; gap: 6px;">
            Estado de Suspensión
            <span style="background: #333; color: #ccc; border-radius: 50%; width: 16px; height: 16px; font-size: 11px; display: inline-flex; align-items: center; justify-content: center; cursor: help;" title="Condición dinámica de estabilidad calculada desde el backend">?</span>
        </div>
        <div style="font-size: 24px; color: white; font-weight: bold; margin-top: 5px;">{status_text}</div>
    </div>
    """
    st.markdown(damping_card_html, unsafe_allow_html=True)

st.markdown("---")

# ===== GRÁFICAS ADICIONALES =====
st.subheader("📈 Análisis de Trayectoria")

col_plot1, col_plot2 = st.columns(2)

with col_plot1:
    fig_x = go.Figure()
    fig_x.add_trace(go.Scatter(
        x=t, y=x,
        mode='lines',
        name='Desplazamiento x(t)',
        line=dict(color='#00ff88', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.15)'
    ))
    fig_x.add_hline(y=0, line_dash="dash", line_color="#ff6b35", line_width=2, annotation_text="Equilibrio")
    fig_x.update_layout(
        template="plotly_dark",
        title="Desplazamiento vs Tiempo",
        xaxis_title="Tiempo (s)",
        yaxis_title="Desplazamiento (m)",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig_x, use_container_width=True)

with col_plot2:
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(
        x=t, y=v,
        mode='lines',
        name='Velocidad v(t)',
        line=dict(color='#ff6b35', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(255, 107, 53, 0.15)'
    ))
    fig_v.add_hline(y=0, line_dash="dash", line_color="#00ff88", line_width=2, annotation_text="v = 0")
    fig_v.update_layout(
        template="plotly_dark",
        title="Velocidad vs Tiempo",
        xaxis_title="Tiempo (s)",
        yaxis_title="Velocidad (m/s)",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ===== ESPACIO DE FASE =====
st.subheader("🔄 Espacio de Fase (Retrato de Fase)")
fig_phase = go.Figure()
fig_phase.add_trace(go.Scatter(
    x=x, y=v,
    mode='lines+markers',
    name='Trayectoria de fase',
    line=dict(color='#00ccff', width=2.5),
    marker=dict(size=3, opacity=0.6),
    hovertemplate='<b>x:</b> %{x:.4f}m<br><b>v:</b> %{y:.4f}m/s<extra></extra>'
))
fig_phase.add_trace(go.Scatter(
    x=[0], y=[0],
    mode='markers',
    name='Punto de Equilibrio',
    marker=dict(size=14, color='#ff00ff', symbol='cross', line=dict(width=2))
))
fig_phase.update_layout(
    template="plotly_dark",
    title="Diagrama de Fase: Velocidad vs Desplazamiento",
    xaxis_title="Desplazamiento x (m)",
    yaxis_title="Velocidad v (m/s)",
    hovermode="closest",
    height=450
)
st.plotly_chart(fig_phase, use_container_width=True)

