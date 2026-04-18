# 🚗 Gemelo Digital: Sistema de Suspensión Masa-Resorte-Amortiguador

<p align="center">
  <img src="assets/suspension_diagram.png" alt="Diagrama Masa-Resorte-Amortiguador" width="400"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white"/>
  <img src="https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white"/>
  <img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge"/>
</p>

Bienvenido al **Gemelo Digital de un Sistema de Suspensión Masa-Resorte-Amortiguador**. Este proyecto ofrece una plataforma interactiva para simular, monitorear y analizar el comportamiento dinámico de una suspensión vehicular, conectando el mundo físico con el digital para **predecir fallas antes de que ocurran en el hardware real**.

---

## 📋 Tabla de Contenidos
- [Descripción](#descripción)
- [Características](#características)
- [Modelo Físico](#modelo-físico)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Uso](#uso)
- [Sistema de Alertas](#sistema-de-alertas-predictivas)
- [Stack Tecnológico](#stack-tecnológico)
- [Licencia](#licencia)
- [Autores](#autores)

---

## 📌 Descripción

Este proyecto implementa un **Gemelo Digital** de una suspensión masa-resorte-amortiguador. Resuelve ecuaciones diferenciales en tiempo real usando **SciPy RK45** y las visualiza en una animación 3D construida con **Three.js**, todo dentro de un dashboard interactivo hecho con **Streamlit**.

El sistema replica digitalmente el comportamiento de una suspensión física, permitiendo detectar cuándo el amortiguador está desgastado **antes de que falle el hardware real**.

---

## ✨ Características

- [x] Visualización 3D del carro con resorte helicoidal y amortiguador hidráulico animados
- [x] Motor de física: resuelve `m·x'' + b·x' + k·x = F(t)` con SciPy RK45
- [x] Sliders interactivos: masa (m), constante del resorte (k), amortiguador (b)
- [x] Gráfica de telemetría en vivo con Plotly (zoom y valores al pasar el mouse)
- [x] Alerta automática si el sistema tarda más de 3 segundos en estabilizarse
- [x] Detección de picos de vibración y exportación a JSON estructurado
- [x] Indicador de estado: Subamortiguado / Amortiguamiento Crítico / Sobreamortiguado
- [x] OrbitControls: rotar y hacer zoom a la escena 3D con el mouse

---

## ⚙️ Modelo Físico

El sistema resuelve esta ecuación diferencial de segundo orden en cada frame:
m·x''(t) + b·x'(t) + k·x(t) = F(t)

| Símbolo | Nombre | Unidad |
|---------|--------|--------|
| m | Masa | kg |
| b | Coeficiente de amortiguamiento | Ns/m |
| k | Constante del resorte | N/m |
| x | Desplazamiento | m |
| F(t) | Fuerza de entrada (bache) | N |

**Frecuencia natural:**
ωn = √(k/m)

**Factor de amortiguamiento:**
ζ = b / (2·ωn·m)

| Condición | Estado | Comportamiento |
|-----------|--------|----------------|
| ζ < 1 | 🔴 Subamortiguado | El sistema oscila tras el bache |
| ζ = 1 | 🟡 Amortiguamiento crítico | Retorno óptimo al equilibrio |
| ζ > 1 | 🟢 Sobreamortiguado | Retorno muy lento |

---

## 🗂️ Estructura del Proyecto
digital-twin-suspension/
├── app.py                    # Dashboard principal (Streamlit)
├── backend/
│   ├── init.py
│   ├── physics.py            # Motor de física con SciPy RK45
│   └── alert_system.py       # Sistema de alertas + exportación JSON
├── frontend/
│   └── component.html        # Animación 3D con Three.js
├── assets/
│   └── car.glb               # Modelo 3D del vehículo
├── requirements.txt          # Dependencias de Python
├── picos_vibracion.json      # Picos de vibración exportados
├── test_alert.py             # Scripts de prueba
├── test_alert2.py
├── updater.py                # Lógica de actualización
└── README.md

---

## 🚀 Instalación

### Requisitos previos
- Python 3.8 o superior
- Se recomienda usar un entorno virtual

### Pasos

**1. Clona el repositorio:**
```bash
git clone https://github.com/AnyeCOsp23/digital-twin-suspension.git
cd digital-twin-suspension
```

**2. Instala las dependencias:**
```bash
pip install -r requirements.txt
```

**3. Ejecuta la aplicación:**
```bash
streamlit run app.py
```

Luego abre tu navegador en: `http://localhost:8501`

---

## 🎮 Uso

1. **Mueve los sliders** del panel izquierdo para cambiar masa, resorte y amortiguador
2. **Presiona ESPACIO** para simular el golpe sobre un bache
3. **Observa** cómo el resorte se comprime y el amortiguador desliza en tiempo real
4. **Monitorea** la gráfica de telemetría en vivo y el estado del sistema
5. **Exporta** los picos de vibración al JSON con el botón de exportar

---

## ⚠️ Sistema de Alertas Predictivas

Si el desplazamiento `x(t)` tarda más de **3 segundos** en estabilizarse dentro de ±0.05m tras el bache, el sistema dispara:
ERROR: Amortiguador desgastado. Requiere mantenimiento

Los picos se guardan automáticamente en `picos_vibracion.json`:

```json
{
  "version_del_modelo": "1.0.0",
  "fecha_exportacion": "2024-01-15T10:30:00",
  "parametros": {
    "masa_kg": 2.0,
    "amortiguador_b": 4.0,
    "resorte_k": 5.0
  },
  "umbral_de_alerta_s": 3.0,
  "total_picos": 4,
  "picos_detectados": [
    { "timestamp": 1.23, "amplitud": 0.87, "peak_index": 123 }
  ]
}
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Visualización 3D | Three.js r128 | Modelo del carro, resorte helicoidal, amortiguador |
| Motor de Física | SciPy / NumPy | Solver de EDO con método RK45 |
| Dashboard | Streamlit | Interfaz, sliders, alertas |
| Gráficas | Plotly | Telemetría en tiempo real |
| Datos | Pandas / JSON | Detección y exportación de picos |

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## 👤 Autores

**Anyelin Ospino**
- GitHub: [@AnyeCOsp23](https://github.com/AnyeCOsp23)

---

*Gemelo Digital para el análisis inteligente y predictivo de sistemas de suspensión vehicular.*

