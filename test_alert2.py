from backend.physics import SuspensionDigitalTwin
from backend.alert_system import check_maintenance_alert

with open("out.txt", "w") as f:
    for damp in [4.0, 0.1]:
        twn = SuspensionDigitalTwin(2.0, damp, 50.0)
        t, x, v = twn.simulate(t_span=(0, 120.0), n_points=4800)
        f.write(f"B={damp}: {check_maintenance_alert(t, x, twn)}\n")