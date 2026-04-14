import numpy as np
from scipy.integrate import solve_ivp

class SuspensionDigitalTwin:
    def __init__(self, m=2.0, b=4.0, k=5.0):
        """
        Digital Twin of a mass-spring-damper suspension system.
        m: Mass (kg)
        b: Damping coefficient (Ns/m)
        k: Spring constant (N/m)
        """
        self.m = m
        self.b = b
        self.k = k

    def _model(self, t, y, F):
        """
        Second-order ODE: m*x'' + b*x' + k*x = F
        State vector y = [position, velocity]
        """
        x, v = y
        acceleration = (F - self.b * v - self.k * x) / self.m
        return [v, acceleration]

    def simulate(self, t_span=(0, 10), n_points=1000, force=1.0):
        """
        Solves the ODE and returns time, position, and velocity arrays.
        """
        t_eval = np.linspace(*t_span, n_points)
        solution = solve_ivp(
            self._model,
            t_span,
            [0.0, 0.0],
            t_eval=t_eval,
            args=(force,),
            method='RK45'
        )
        return t_eval, solution.y[0], solution.y[1]

    def get_system_info(self):
        """
        Returns natural frequency (wn) and damping ratio (zeta).
        """
        wn   = np.sqrt(self.k / self.m)
        zeta = self.b / (2 * wn * self.m)

        if zeta < 1:
            status = "Underdamped 🔴"
        elif abs(zeta - 1) < 0.001:
            status = "Critically damped 🟡"
        else:
            status = "Overdamped 🟢"

        return {
            "wn":     round(wn,   4),
            "zeta":   round(zeta, 4),
            "status": status
        }
        