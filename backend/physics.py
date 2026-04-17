import numpy as np
from scipy.integrate import solve_ivp

class SuspensionDigitalTwin:
    def __init__(self, m=2.0, b=4.0, k=5.0):
        self.m = m
        self.b = b
        self.k = k
        self.random_bumps = []
        
    def _generate_random_bumps(self, max_time, exact_num_bumps=None):
        self.random_bumps = []
        
        if exact_num_bumps is not None:
            if exact_num_bumps == 0:
                return
            t = 5.0
            while t < max_time - 5.0:
                for _ in range(exact_num_bumps):
                    if t >= max_time - 5.0:
                        break
                    dur = np.random.uniform(0.15, 0.35)
                    self.random_bumps.append((t, t + dur))
                    t += dur + np.random.uniform(0.2, 0.8) # Espacio corto entre baches consecutivos
                
                t += np.random.uniform(3.0, 10.0) # Espacio largo antes del siguiente grupo
            return
            
        t = 5.0  
        # Evitamos baches en los últimos 5 segundos para que la suspensión 
        # se estabilice a 0.0 exactos antes de que el ciclo se reinicie
        while t < max_time - 5.0:
            # Hacer grupos o baches solitarios al azar (1 a 4 baches seguidos)
            num_in_cluster = np.random.randint(1, 5)
            for _ in range(num_in_cluster):
                if t >= max_time - 5.0:
                    break
                dur = np.random.uniform(0.15, 0.35)
                self.random_bumps.append((t, t + dur))
                # Espacio corto (o algo aleatorio) entre baches del mismo grupo
                t += dur + np.random.uniform(0.2, 0.8)
            
            # Espacio largo y aleatorio sin baches tras el grupo
            t += np.random.uniform(3.0, 10.0)

    def _model(self, t, y, bump_height):
        x, v = y
        force_externa = 0.0
        for b_start, b_end in self.random_bumps:
            if b_start <= t <= b_end:
                # La fuerza del bache es menor para que los defaults no lo rompan
                force_externa = 50.0 * bump_height
                break
                
        # Si k es grande, el término (-k*x) devuelve el auto rápidamente a 0
        acceleration = (force_externa - self.b * v - self.k * x) / self.m
        return [v, acceleration]

    def simulate(self, t_span=(0, 105.0), n_points=3500, bump_height=0.15, exact_num_bumps=None):      
        # Generar 1 HORA (3600s) de baches para que el frontend pueda rodar infinitamente sin loops
        self._generate_random_bumps(3600.0, exact_num_bumps=exact_num_bumps)
        self.is_broken = False
        t_eval = np.linspace(*t_span, n_points)
        solution = solve_ivp(
            self._model,
            t_span,
            [0.0, 0.0],
            t_eval=t_eval,
            args=(bump_height,),
            method='RK45',
            max_step=0.05
        )
        
        x = solution.y[0]
        v = solution.y[1]
        
        # Detectar ruptura mecánica (ej. desplazamiento excesivo del amortiguador)
        for i in range(len(x)):
            if abs(x[i]) > 0.4:  # Umbral de ruptura superado
                self.is_broken = True
                breaker_idx = i
                break
                
        if self.is_broken:
            # Sobrescribir el resto del arreglo tras la ruptura
            # El carro se desploma (máxima compresión x = +0.33) y se queda rígido
            for i in range(breaker_idx, len(x)):
                x[i] = 0.33
                v[i] = 0.0

        return t_eval, x, v

    def get_system_info(self):
        wn   = np.sqrt(self.k / self.m)
        zeta = self.b / (2 * wn * self.m)

        if getattr(self, 'is_broken', False):
            status = "AMORTIGUADOR ROTO 💥"
        elif zeta < 0.95:
            status = "Subamortiguado (Oscila y tarda en estabilizar)"
        elif zeta <= 1.05:
            status = "Críticamente amortiguado (Estabiliza rápido)"
        else:
            status = "Sobreamortiguado (Baja y tarda en subir)"

        return {
            "wn":     round(wn,   4),
            "zeta":   round(zeta, 4),
            "status": status
        }