import os

html_code = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #0d0d0d; font-family: 'Courier New', monospace; }
        canvas { display: block; width: 100vw; height: 100vh; }
        #hud {
            position: absolute; top: 15px; left: 15px; color: #00FF00;
            background: rgba(0, 0, 0, 0.7); padding: 15px; border: 1px solid #00FF00; border-radius: 5px; box-shadow: 0 0 10px #00FF00; pointer-events: none; z-index: 1000;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="hud">
        <strong style="color:#fff">DIGITAL TWIN 3D ENGINE</strong><br>
        STATUS: <span style="color:#0f0">ONLINE</span><br>
        MODE: LIVE TELEMETRY<br>
        Y-DISP: <span id="disp_hud">0.000</span> m
    </div>
    <script>
        let trajectory = __TRAJECTORY_DATA__;
        let times = __TIME_DATA__;
        const BUMPS = __BUMPS_DATA__;
        
        let frame = 0; let currentDisp = 0;
        
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x0d0d0d, 0.015);
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(-15, 8, 20); camera.lookAt(0, 2, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.4));
        const spotLight = new THREE.SpotLight(0xffffff, 2.5);
        spotLight.position.set(10, 30, 20); spotLight.castShadow = true;
        scene.add(spotLight);
        const fillLight = new THREE.DirectionalLight(0x00E5FF, 0.8); 
        fillLight.position.set(-20, 10, -20); scene.add(fillLight);

        const floor = new THREE.Mesh(new THREE.PlaneGeometry(300, 100), new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9, metalness: 0.2 }));
        floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
        const grid = new THREE.GridHelper(300, 150, 0x333333, 0x111111); grid.position.y = 0.05; scene.add(grid);

        const carGroup = new THREE.Group(); scene.add(carGroup);

        const chassis = new THREE.Mesh(new THREE.BoxGeometry(11, 2.2, 4.8), new THREE.MeshPhysicalMaterial({ color: 0xc0c0c0, metalness: 0.8, roughness: 0.2, clearcoat: 1.0, clearcoatRoughness: 0.1 }));
        chassis.position.y = 3.5; chassis.castShadow = true; carGroup.add(chassis);

        const cabin = new THREE.Mesh(new THREE.BoxGeometry(5.5, 1.6, 4.2), new THREE.MeshPhysicalMaterial({ color: 0x050505, metalness: 0.9, roughness: 0.1, transmission: 0.6 }));
        cabin.position.set(-0.5, 5.4, 0); cabin.castShadow = true; carGroup.add(cabin);

        const tailLight = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.6, 4.4), new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 2 }));
        tailLight.position.set(-5.5, 3.5, 0); carGroup.add(tailLight);

        const headLight = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.6, 4.4), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 5 }));
        headLight.position.set(5.5, 3.3, 0); carGroup.add(headLight);

        const wheelRadius = 1.4;
        const wheelGeo = new THREE.CylinderGeometry(wheelRadius, wheelRadius, 1.2, 32);
        const tireMat = new THREE.MeshStandardMaterial({ color: 0x0a0a0a, roughness: 0.9 });
        const rimMat = new THREE.MeshStandardMaterial({ color: 0xeeeeee, metalness: 1.0, roughness: 0.2 });
        
        const wheels = []; const springs = [];
        const wPos = [[-3.5, wheelRadius, 2.6], [3.5, wheelRadius, 2.6], [-3.5, wheelRadius, -2.6], [3.5, wheelRadius, -2.6]];

        class HelixCurve extends THREE.Curve {
            constructor(r, c, h) { super(); this.r=r; this.c=c; this.h=h; }
            getPoint(t, opt) { const a=t*Math.PI*2*this.c; return (opt||new THREE.Vector3()).set(Math.cos(a)*this.r, t*this.h, Math.sin(a)*this.r); }
        }
        const springGeo = new THREE.TubeGeometry(new HelixCurve(0.4, 6, 2.5), 64, 0.1, 8, false);
        const springMat = new THREE.MeshStandardMaterial({ color: 0xe91e63, metalness: 0.6, roughness: 0.3 }); 

        wPos.forEach(p => {
            const wG = new THREE.Group(); wG.position.set(...p);
            const tire = new THREE.Mesh(wheelGeo, tireMat); tire.rotation.x = Math.PI/2; tire.castShadow = true; wG.add(tire);
            const rim = new THREE.Mesh(new THREE.CylinderGeometry(wheelRadius*0.6, wheelRadius*0.6, 1.25, 16), rimMat); rim.rotation.x = Math.PI/2; wG.add(rim);
            scene.add(wG); wheels.push(wG);
            const spring = new THREE.Mesh(springGeo, springMat); spring.position.set(...p); scene.add(spring); springs.push(spring);
        });

        const bumpMeshes = [];
        const bumpGeo = new THREE.CylinderGeometry(0.6, 0.6, 30, 32);
        const bumpMat = new THREE.MeshStandardMaterial({ color: 0xFFD600, roughness: 0.6 }); 
        if (Array.isArray(BUMPS)) {
            BUMPS.forEach(b => {
                const bM = new THREE.Mesh(bumpGeo, bumpMat); bM.rotation.z = Math.PI/2; bM.position.y = -0.2; bM.castShadow = true;
                scene.add(bM); bumpMeshes.push({ m: bM, s: b.s, e: b.e });
            });
        }

        let currentT = 0; const SPEED = 25; 
        function animate() {
            requestAnimationFrame(animate);
            if (trajectory && times && trajectory.length > 0) { currentT = times[frame]; currentDisp = trajectory[frame]; frame = (frame+1)%trajectory.length; } else { currentT+=0.02; }

            document.getElementById('disp_hud').innerText = currentDisp.toFixed(4);
            const chY = 3.5 - (currentDisp * 6.0);
            chassis.position.y = chY; cabin.position.y = chY + 1.9; tailLight.position.y = chY; headLight.position.y = chY - 0.2;
            grid.position.x = -(currentT * SPEED) % 15;
            
            bumpMeshes.forEach(b => { b.m.position.x = 15 - ((currentT - b.s) * SPEED); });

            wheels.forEach((w, i) => {
                w.children[0].rotation.y -= 0.15; w.children[1].rotation.y -= 0.15;
                let wy = wheelRadius;
                bumpMeshes.forEach(b => {
                    if (currentT >= b.s && currentT <= b.e) { wy += 0.9 * (1.0 - Math.pow(Math.abs(currentT - (b.s+b.e)/2)/((b.e-b.s)/2), 2)); }
                });
                w.position.y = wy;
                const sp = springs[i]; sp.position.y = w.position.y; sp.scale.y = Math.max(0.1, (chY - 0.5 - w.position.y)/2.5);
            });
            renderer.render(scene, camera);
        }
        animate();
        window.addEventListener('resize', () => { camera.aspect = window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
    </script>
</body>
</html>"""

app_code = """import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import sys
import os
import json
import streamlit.components.v1 as components

sys.path.append(os.path.dirname(__file__))

try:
    from backend.physics import SuspensionDigitalTwin
    from backend.alert_system import check_maintenance_alert, export_peaks_json
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.stop()

st.set_page_config(page_title="3D Digital Twin", layout="wide", page_icon="🏎️")
st.markdown('''<style>
.main { background-color: #0e1117; }
</style>''', unsafe_allow_html=True)
st.title("🏎️ Digital Twin 3D: Suspensión Deportiva PRO")

st.sidebar.markdown("### Configuración de Suspensión")

modo_amortiguacion = st.sidebar.radio(
    "Damping Mode",
    ["Manual", "Subamortiguado (Underdamped)", "Crítico (Critically damped)", "Sobreamortiguado (Overdamped)"]
)

if modo_amortiguacion == "Manual":
    m = st.sidebar.slider("Chassis Mass (kg)", 0.5, 10.0, 2.0)
    k = st.sidebar.slider("Spring Constant (k)", 1.0, 100.0, 50.0)
    b = st.sidebar.slider("Damping Coefficient (b)", 0.1, 20.0, 4.0)
elif "Subamortiguado" in modo_amortiguacion:
    m, k, b = 2.0, 50.0, 2.0
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")
elif "Crítico" in modo_amortiguacion:
    m, k, b = 2.0, 50.0, 20.0
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")
else:
    m, k, b = 2.0, 10.0, 80.0
    st.sidebar.info(f"**Valores predefinidos:**\n- Masa (m): {m} kg\n- Resorte (k): {k} N/m\n- Amortiguador (b): {b} Ns/m")

st.sidebar.markdown("---")

modo_baches = st.sidebar.radio(
    "Generación de Baches",
    ["Aleatorios (Infinita)", "Cantidad Exacta"]
)
if modo_baches == "Cantidad Exacta":
    exact_baches = st.sidebar.number_input("Número de Baches", min_value=0, max_value=50, value=3, step=1)
else:
    exact_baches = None

if 'sim_params' not in st.session_state or st.session_state.sim_params != (m, b, k, exact_baches):
    st.session_state.sim_params = (m, b, k, exact_baches)
    twin = SuspensionDigitalTwin(m, b, k)
    t, x, v = twin.simulate(t_span=(0, 20.0), n_points=800, exact_num_bumps=exact_baches)
    st.session_state.twin_cached = (twin, t, x, v)
    st.session_state.start_time_sync = int(time.time() * 1000) + 150
else:
    twin, t, x, v = st.session_state.twin_cached

info = twin.get_system_info()

col1, col2, col3 = st.columns(3)
col1.metric("Natural Frequency (ωn)", f"{info['wn']} rad/s")
col2.metric("Damping Ratio (ζ)", f"{info['zeta']}")
col3.metric("System Status", info['status'])

st.markdown("---")
c_3d, c_graph = st.columns([1.5, 1])

with c_3d:
    st.subheader("Visor Industrial de Gemelo Digital 3D")
    try:
        with open("frontend/component.html", "r", encoding="utf-8") as f:
            html_3d = f.read()
        html_3d = html_3d.replace('__TRAJECTORY_DATA__', json.dumps(x.tolist()))
        html_3d = html_3d.replace('__TIME_DATA__', json.dumps(t.tolist()))
        bumps = [{"s": bb[0], "e": bb[1]} for bb in twin.random_bumps] if hasattr(twin, 'random_bumps') else []
        html_3d = html_3d.replace('__BUMPS_DATA__', json.dumps(bumps))
        components.html(html_3d, height=550)
    except Exception as e:
        st.error(f"Error cargando componente: {e}")

with c_graph:
    st.subheader("📡 Live Telemetry (Streaming Plotly)")
    graph_placeholder = st.empty()
    window_size = 90
    for i in range(10, min(800, len(t)), 15):
        start_idx = max(0, i - window_size)
        fig = go.Figure(go.Scatter(x=t[start_idx:i], y=x[start_idx:i], mode='lines', line=dict(color='#00E5FF', width=3)))
        t_start = float(t[start_idx])
        t_end = t_start + (window_size * (20.0/800.0))
        fig.update_layout(
            template="plotly_dark", plot_bgcolor='#111111', paper_bgcolor='#111111',
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(range=[t_start, t_end], showgrid=False),
            yaxis=dict(range=[-1.5, 1.5], showgrid=True, gridcolor='#333', zerolinecolor='#e91e63'),
            height=450
        )
        graph_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.01)

if st.sidebar.button("📁 Export Vibration Peaks"):
    peaks_file = export_peaks_json(t, x)
    with open(peaks_file, "r") as f:
        st.sidebar.download_button("Descargar JSON", f.read(), file_name="peaks.json", mime="application/json")
    st.sidebar.success("Log generado.")
"""

with open("c:/Users/HP245-G8/digital-twin-suspension-/frontend/component.html", "w", encoding="utf-8") as f:
    f.write(html_code)

with open("c:/Users/HP245-G8/digital-twin-suspension-/app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Files updated!")