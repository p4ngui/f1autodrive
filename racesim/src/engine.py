import math

import numpy as np
from matplotlib import pyplot as plt


class Engine():

    def __init__(self):
        super().__init__()
    # topology:                     [-] RWD or AWD or FWD
    # pow_max:                      [W] maximum power
    # pow_diff:                     [W] power drop from maximum power at n_begin and n_end
    # n_begin:                      [1/min] engine rpm at pow_max - pow_diff
    # n_max:                        [1/min] engine rpm at pow_max
    # n_end:                        [1/min] engine rpm at pow_max -
    #   pow_diff -> should be greater than n_shift!
    # be_max:                       [kg/h] fuel consumption
    # pow_e_motor:                  [W] total electric motor power
    #   (after efficiency losses)
    # eta_e_motor:                  [-] efficiency electric motor (drive)
    # eta_e_motor_re:               [-] efficiency electric motor (recuperation)
    # eta_etc_re:                   [-] efficiency electric turbocharger (recuperation)
    # vel_min_e_motor:              [m/s] minimum velocity to use electric motor
    # torque_e_motor_max:           [Nm] maximum torque of electric motor
    #   (after efficiency losses)

        self.HP_combustion_max = 701e3
        self.HP_electric_max = 120e3
        self.RPM_min = 1000
        self.RPM_max = 11400.0
        self.RPM_end = 12200.0
        self.topology = "RWD"
        self.pow_max = self.HP_combustion_max
        self.pow_diff = 41e3
        self.pow_e_motor = self.HP_electric_max
        self.eta_e_motor = 0.9
        self.eta_e_motor_re = 0.15
        self.eta_etc_re = 0.10
        self.vel_min_e_motor = 27.777
        self.torque_e_motor_max = 200.0
        self.pow_begend = self.pow_max - self.pow_diff
        self.max_temp_water = 150  # [°Celsius]
        self.max_temp_internal = 1000  # [°Celsius]
        self.n_begin = 10500.0 / 60.0
        self.n_max = self.RPM_max / 60.0
        self.n_end = self.RPM_end / 60.0
        self.be_max = 100.0 / 3600.0
        # State vars
        self.rpm = 0
        self.hp = 0
        self.z_pow_engine = 0
        self.z_pow_engine = self.ice_power()
        self.temp_internal = 200
        self.temp_water = 50
        self.health = 100.0

    def ice_power(self):
        a = np.array([[math.pow(self.n_begin, 3), math.pow(self.n_begin, 2), self.n_begin,
                       1], [3 * math.pow(self.n_max, 2), 2 * self.n_max, 1, 0],
                     [math.pow(self.n_max, 3), math.pow(self.n_max, 2), self.n_max, 1],
                     [math.pow(self.n_end, 3), math.pow(self.n_end, 2), self.n_end, 1]])
        b = np.array([[self.pow_begend], [0], [self.pow_max], [self.pow_begend]])

        return np.linalg.solve(a, b)

    def power_engine(self, n: float or np.ndarray):
        """
        Power curve is approximated by a peak power pow_max at n_max and equal drops on
            both sides at n_begin and n_end.
        Rev input is in 1/s, output is in W.
        """
        # Update RPM
        self.rpm = n
        # limit engine speed to valid range of power curve
        n_use = np.copy(n)
        n_use[n_use < 0.75 * self.n_begin] = 0.75 * self.n_begin
        n_use[n_use > 1.2 * self.n_end] = 1.2 * self.n_end

        # calculate power
        p_eng = (self.z_pow_engine[0] * np.power(n_use, 3)
                 + self.z_pow_engine[1] * np.power(n_use, 2)
                 + self.z_pow_engine[2] * n_use + self.z_pow_engine[3])
        p_eng[p_eng < 0.0] = 0.0  # assure that no negative powers appear

        return p_eng

    def torque_e_motor(self, n: float):
        """Rev input in 1/s. Output is the maximum torque in Nm."""
        torque_tmp = self.pow_e_motor / (2 * math.pi * n)
        return min(torque_tmp, self.torque_e_motor_max)

    def torque(self, n: float):
        # Rev input in 1/s. Output is the maximum torque in Nm.
        return float(self.power_engine(n=n)) / (2 * math.pi * n)

    def fuel_cons(self, t_cl: np.ndarray, n_cl: np.ndarray, m_eng: np.ndarray):
        # bRev input in 1/s, torque input in Nm. Output is the consumed fuel mass
        #   until the current point in kg
        # (closed).

        be_kgs = self.injectionmap(n=n_cl[:-1], m_eng=m_eng)  # [kg/s]
        # integrate
        consumpt_kg_part = np.diff(t_cl) * be_kgs

        return np.insert(np.cumsum(consumpt_kg_part), 0, 0.0)  # consumpt_kg_cl [kg]

    def injectionmap(self, n: np.ndarray, m_eng: np.ndarray):
        # Rev input in 1/s, torque input in Nm. Output is in kg/s.
        # Model of the engine fuel consumption.

        pow_actual = 2 * math.pi * n * m_eng  # [W]
        pow_max = self.power_engine(n=n)    # [W]

        return np.sqrt(pow_actual / pow_max) * self.be_max  # be [kg/s]

    def plot_power_engine(self):
        # plot
        n_range = np.arange(7000.0, 15100.0, 100.0) / 60.0  # [1/s]
        plt.figure()
        plt.plot(n_range * 60.0, self.power_engine(n=n_range) / 1000.0 * 1.36)
        plt.title("Engine power characteristics")
        plt.xlabel("n in 1/min")
        plt.ylabel("P in PS")

        plt.show()

    def e_cons(self, t_cl: np.ndarray, n_cl: np.ndarray, m_e_motor: np.ndarray):
        # Rev input in 1/s, torque input in Nm.
        # Output is the consumed energy in J until the current point(closed).
        # Calculates used energy including the efficiency.

        be_w = self.power_demand_e_motor_drive(n=n_cl[:-1], m_e_motor=m_e_motor)  # [W]

        # integrate
        e_consumpt_j_part = np.diff(t_cl) * be_w  # [J]
        return np.insert(np.cumsum(e_consumpt_j_part), 0, 0.0)

    def power_demand_e_motor_drive(self, n: np.ndarray, m_e_motor: np.ndarray):
        # Rev input in 1/s, torque input in Nm.
        # Output is in W. Calculates used power including the efficiency.

        return (2 * math.pi * n * m_e_motor) / self.eta_e_motor

    def calc_torque_distr(self, n: float, m_requ: float, throttle_pos: float, es: float,
                          em_boost_use: bool, vel: float):
        # n in 1/s, torque_req in Nm, es in J.
        # Function returns torques delivered by engine and e motor in Nm.

        # get torque potential of engine and e motor
        eng_torque_max = self.torque(n=n)
        e_motor_torque_max = self.torque_e_motor(n=n)

        if m_requ <= eng_torque_max:  # ICE only
            m_eng = throttle_pos * m_requ
            m_e_motor = 0.0

        elif m_requ <= eng_torque_max + e_motor_torque_max:  # ICE + e motor (partly)
            m_eng = throttle_pos * eng_torque_max

            if es > 0.0 and em_boost_use and vel >= self.vel_min_e_motor:
                m_e_motor = throttle_pos * (m_requ - eng_torque_max)
            else:
                m_e_motor = 0.0

        else:  # ICE + e motor (fully)
            m_eng = throttle_pos * eng_torque_max

            if es > 0.0 and em_boost_use and vel >= self.vel_min_e_motor:
                m_e_motor = throttle_pos * e_motor_torque_max
            else:
                m_e_motor = 0.0

        return m_eng, m_e_motor

    def calc_torque_distr_f_x(self, f_x: float, n: float, throttle_pos: float, es: float,
                              em_boost_use: bool, vel: float):
        # n in 1/s, torque_req in Nm, es in J.
        # Function returns torques delivered by engine and e motor in Nm.

        # calculate required torque to reach f_x
        m_requ = self.calc_m_requ(f_x=f_x, vel=vel)

        # get torque potential of engine and e motor
        m_eng, m_e_motor = self.calc_torque_distr(n=n,
                                                  m_requ=m_requ,
                                                  throttle_pos=throttle_pos,
                                                  es=es,
                                                  em_boost_use=em_boost_use,
                                                  vel=vel)

        return m_requ, m_eng, m_e_motor

    def calc_m_requ(self, f_x: float, vel: float):
        """Function to calculate required powertrain torque to reach a specific
        longitudinal acceleration force f_x at the current velocity. Input f_x in N,
        vel in m/s. Output is the required powertrain torque in Nm.
        """

        # get gear at velocity
        gear = self.find_gear(vel=vel)[0]

        # m_requ --> calculate powertrain torque
        return (f_x * self.r_driven_tire(vel=vel) * self.pars_gearbox["i_trans"][gear]
                * self.pars_gearbox["e_i"][gear] / self.pars_gearbox["eta_g"])


engine = Engine()
rpm = 7500
pow1 = engine.power_engine(rpm/60)
pow2 = engine.torque_e_motor(rpm/60)
torq = engine.torque(rpm/60)
m_requ = engine.torque(12200/60)
torq2 = engine.calc_torque_distr(rpm/60, m_requ=m_requ,
                                 throttle_pos=1,
                                 es=0,
                                 em_boost_use=False,
                                 vel=120*3.6)
engine.plot_power_engine()
fuel = engine.fuel_cons(torq, [rpm/60], 1)
a = 1
