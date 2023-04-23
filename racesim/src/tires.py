import numpy as np
import matplotlib.pyplot as plt
import math

class Tires():

    def __init__(self, compound: str, age: int, tireset_pars: dict):
        super().__init__()
        # tire_model_exp:               [-] exponent used in the tire model to adjust
        #                 
        # F1 2023 sizes in mm/"   Front: 305mm/720mm-18   Rear: 405mm/720mm-18
        # shape of friction "circle" -> [1.0, 2.0]
        self.tire_model_exp = 2.0
        # lf:                           [m] x distance front axle to center of gravity
        # lr:                           [m] x distance rear axle to center of gravity
        # h_cog:                        [m] height of center of gravity
        # sf:                           [m] track width front
        # sr:                           [m] track width rear
        # m:                            [kg] vehicle mass inlcuding driver excluding fuel
        #                                    (F1 minimum 728kg)
        # f_roll:                       [-] rolling resistance coefficient
        # c_w_a:                        [m^2] c_w * A_car -> air resistance calculation
        # c_z_a_f:                      [m^2] c_z_f * A_frontwing
        # c_z_a_r:                      [m^2] c_z_r * A_rearwing
        # g:                            [m/s^2]
        # rho_air:                      [kg/m^3] air density
        # drs_factor:                   [-] part of reduction of air resistance by DRS
        # mu_mean:                      [-] mean friction value of track
        self.mu = 1.0
        self.lf = 1.968
        self.lr = 1.632
        self.l_tot = self.lf + self.lr
        # car value
        # TODO move to car class & pass it as param
        self.h_cog = 0.335
        self.topology = "RWD"
        self.sf = 1.6
        self.sr = 1.6
        self.m = 796.0
        self.f_roll = 0.03
        # aero
        self.c_w_a = 1.56
        self.c_z_a_f = 2.20
        self.c_z_a_r = 2.68
        self.g = 9.81
        self.rho_air = 1.18
        self.drs_factor = 0.17

        self.f_z_calc_stat = {}
        self.f_z_fl = None
        self.f_z_fr = None
        self.f_z_rl = None
        self.f_z_rr = None
        self.f_z_calc_stat["stat_load"] = np.zeros(4)
        self.f_z_calc_stat["aero"] = np.zeros(4)
        self.f_z_calc_stat["trans_long"] = np.zeros(4)
        self.f_z_calc_stat["trans_lat"] = np.zeros(4)

        self.init_front()
        self.init_rear()
        # calculate static parts of tire load calculation
        self.static_load()
        self.trans_long()
        self.trans_lar()
        self.aero()
        # compound, e.g. A3 A4 A5
        self.compound = compound
        # [-] tireset age in laps (total)
        self.age_tot = age
        # [-] tireset age in laps (current stint)
        self.age_curstint = 0
        # [-] tireset age in laps ("virtual" age for tire deg. calculation)
        self.age_degr = float(age)
        # [-] tireset parameters for current compound (driver-specific)
        self.tireset_pars = tireset_pars

    def static_load(self):
        # static load
        self.f_z_calc_stat["stat_load"][0] = 0.5 * self.m * self.g * self.lr / self.l_tot
        self.f_z_calc_stat["stat_load"][1] = 0.5 * self.m * self.g * self.lr / self.l_tot
        self.f_z_calc_stat["stat_load"][2] = 0.5 * self.m * self.g * self.lf / self.l_tot
        self.f_z_calc_stat["stat_load"][3] = 0.5 * self.m * self.g * self.lf / self.l_tot

    def trans_long(self):
        # longitudinal load transfer
        self.f_z_calc_stat["trans_long"][0] = (0.5 * self.m * self.h_cog) / self.l_tot
        self.f_z_calc_stat["trans_long"][1] = (0.5 * self.m * self.h_cog) / self.l_tot
        self.f_z_calc_stat["trans_long"][2] = (0.5 * self.m * self.h_cog) / self.l_tot
        self.f_z_calc_stat["trans_long"][3] = (0.5 * self.m * self.h_cog) / self.l_tot

    def trans_lar(self):
        # lateral load transfer
        self.f_z_calc_stat["trans_lat"][0] = (self.m * self.lr) / (
            self.l_tot * self.h_cog) / self.sf
        self.f_z_calc_stat["trans_lat"][1] = (self.m * self.lr) / (
            self.l_tot * self.h_cog) / self.sf
        self.f_z_calc_stat["trans_lat"][2] = (self.m * self.lf) / (
            self.l_tot * self.h_cog) / self.sr
        self.f_z_calc_stat["trans_lat"][3] = (self.m * self.lf) / (
            self.l_tot * self.h_cog) / self.sr

    def aero(self):
        # aero downforce
        self.f_z_calc_stat["aero"][0] = 0.5 * 0.5 * self.c_z_a_f * self.rho_air
        self.f_z_calc_stat["aero"][1] = 0.5 * 0.5 * self.c_z_a_f * self.rho_air
        self.f_z_calc_stat["aero"][2] = 0.5 * 0.5 * self.c_z_a_r * self.rho_air
        self.f_z_calc_stat["aero"][3] = 0.5 * 0.5 * self.c_z_a_r * self.rho_air

    def init_front(self):
        # tire data should be normalized to mu = 1.0 (coefficient of friction of the
        # track / tire test bench)
        # circ_ref:                     [m] loaded reference circumreference
        # fz_0:                         [N] nominal tire load
        # mux:                          [-] corresponds to the coefficient of friction at
        #                                   nominal tire load (fz == fz_0)
        # muy:                          [-] corresponds to the coefficient of friction at
        #                                   nominal tire load (fz == fz_0)
        # dmux_dfz:                     [-] reduction of force potential with rising tire
        #                                   load (fz > fz_0) -> negative value!
        # dmuy_dfz:                     [-] reduction of force potential with rising tire
        #                                   load (fz > fz_0) -> negative value!

        self.f_circ_ref = 2.262
        self.f_fz_0 = 3000.0
        self.f_mux = 1.65
        self.f_muy = 1.85
        self.f_dmux_dfz = -5.0e-5
        self.f_dmuy_dfz = -5.0e-5

    def init_rear(self):
        self.r_circ_ref = 2.262
        self.r_fz_0 = 3000.0
        self.r_mux = 1.95
        self.r_muy = 2.15
        self.r_dmux_dfz = -5.0e-5
        self.r_dmuy_dfz = -5.0e-5

    def check_tire_loads(self):
        # check tire loads
        """
        Commented since it often happens with the FB+ solver that very high lateral
        accelerations and therefore tire loads appear when it runs into a corner,
        i.e. a high curvature. As the tires limit the lateral acceleration due
        to their limited force potential afterwards this is usually not a problem.
        Use the lateral acceleration plot
        and the tire loads plot at the end of the calculation to check the validity
        of the lateral accelerations appearing.
        """

        # print("WARNING: Very small tire load FL!")
        self.f_z_fl = max(self.f_z_fl, 30.0)
        # print("WARNING: Very small tire load FR!")
        self.f_z_fr = max(self.f_z_fr, 30.0)
        # print("WARNING: Very small tire load RL!")
        self.f_z_rl = max(self.f_z_rl, 30.0)
        # print("WARNING: Very small tire load RR!")
        self.f_z_rr = max(self.f_z_rr, 30.0)

    def tire_force_potentials(self, vel: float, a_x: float, a_y: float):
        """
        The function is used to calculate the transmitted tire forces depending on the
        current longitudinal and lateral
        accelerations and velocity.
        Velocity input in m/s, accelerations in m/s^2. Calculates the currently
        acting tire loads f_z (considering dynamic load transfers) and the force
        potentials f_t of all four tires. Vehicle coordinate system: x - front,
        y - left, z - up. The tire model includes the reduction of the force potential
        with rising tire loads as tire_par2 are negativ.
        """

        # tire load calculation: static load, longitudinal load transfer,
        # lateral load transfer, aero downforce
        self.f_z_fl = (self.f_z_calc_stat["stat_load"][0]
                       - a_x * self.f_z_calc_stat["trans_long"][0]
                       - a_y * self.f_z_calc_stat["trans_lat"][0]
                       + pow(vel, 2) * self.f_z_calc_stat["aero"][0])
        self.f_z_fr = (self.f_z_calc_stat["stat_load"][1]
                       - a_x * self.f_z_calc_stat["trans_long"][1]
                       + a_y * self.f_z_calc_stat["trans_lat"][1]
                       + pow(vel, 2) * self.f_z_calc_stat["aero"][1])
        self.f_z_rl = (self.f_z_calc_stat["stat_load"][2]
                       + a_x * self.f_z_calc_stat["trans_long"][2]
                       - a_y * self.f_z_calc_stat["trans_lat"][2]
                       + pow(vel, 2) * self.f_z_calc_stat["aero"][2])
        self.f_z_rr = (self.f_z_calc_stat["stat_load"][3]
                       + a_x * self.f_z_calc_stat["trans_long"][3]
                       + a_y * self.f_z_calc_stat["trans_lat"][3]
                       + pow(vel, 2) * self.f_z_calc_stat["aero"][3])

        self.check_tire_loads()

        # tire force potentials
        # (dmux_dfz and dmuy_dfz are negativ -> quadratic malus in the force)
        """
        The function is derived as follows:
        F_x = mu_weather/track * mu_tire(F_z) * F_z (mu_tire hereby not constant as it
        decreases with rising tire loads) = mu_weather/track * (mu_tire + dmu_tire/dF_z
        * (F_z - F_z0)) * F_z (dmu_tire/dF_z is negative)
        """
        self.f_x_pot_fl = self.mu * (self.f_mux + self.f_dmux_dfz
                                     * (self.f_z_fl - self.f_fz_0)) * self.f_z_fl
        self.f_y_pot_fl = self.mu * (self.f_muy + self.f_dmuy_dfz
                                     * (self.f_z_fl - self.f_fz_0)) * self.f_z_fl

        self.f_x_pot_fr = self.mu * (self.f_mux + self.f_dmux_dfz
                                     * (self.f_z_fr - self.f_fz_0)) * self.f_z_fr
        self.f_y_pot_fr = self.mu * (self.f_muy + self.f_dmuy_dfz
                                     * (self.f_z_fr - self.f_fz_0)) * self.f_z_fr

        self.f_x_pot_rl = self.mu * (self.r_mux + self.r_dmux_dfz
                                     * (self.f_z_rl - self.r_fz_0)) * self.f_z_rl
        self.f_y_pot_rl = self.mu * (self.r_muy + self.r_dmuy_dfz
                                     * (self.f_z_rl - self.r_fz_0)) * self.f_z_rl

        self.f_x_pot_rr = self.mu * (self.r_mux + self.r_dmux_dfz
                                     * (self.f_z_rr - self.r_fz_0)) * self.f_z_rr
        self.f_y_pot_rr = self.mu * (self.r_muy + self.r_dmuy_dfz
                                     * (self.f_z_rr - self.r_fz_0)) * self.f_z_rr

        return (self.f_x_pot_fl, self.f_y_pot_fl, self.f_z_fl,
                self.f_x_pot_fr, self.f_y_pot_fr, self.f_z_fr,
                self.f_x_pot_rl, self.f_y_pot_rl, self.f_z_rl,
                self.f_x_pot_rr, self.f_y_pot_rr, self.f_z_rr)

    def plot_tire_characteristics(self):
        # calculate relevant data
        f_z_range = np.arange(500.0, 13000.0, 500.0)

        f_x_f = (self.f_mux
                 + self.f_dmux_dfz
                 * (f_z_range - self.f_fz_0)) * f_z_range
        f_y_f = (self.f_muy
                 + self.f_dmuy_dfz
                 * (f_z_range - self.f_fz_0)) * f_z_range
        f_x_r = (self.r_mux
                 + self.r_dmux_dfz
                 * (f_z_range - self.r_fz_0)) * f_z_range
        f_y_r = (self.r_muy
                 + self.r_dmuy_dfz
                 * (f_z_range - self.r_fz_0)) * f_z_range

        # plot
        plt.figure()

        plt.plot(f_z_range, f_x_f)
        plt.plot(f_z_range, f_y_f)
        plt.plot(f_z_range, f_x_r)
        plt.plot(f_z_range, f_y_r)

        plt.grid()
        plt.title("Tire force characteristics")
        plt.xlabel("F_z in N")
        plt.ylabel("Forces F_x and F_y in N")
        plt.legend(["F_x front", "F_y front", "F_x rear", "F_y rear"])

        plt.show()

    def circumref_driven_tire(self, vel: float):
        """Velocity input in m/s. Reference speed for the circumreference calculation
        is 60 km/h. Output is in m."""

        if self.topology == "FWD":
            tire_circ_ref = self.f_circ_ref

        elif self.topology == "RWD":
            tire_circ_ref = self.r_circ_ref

        elif self.topology == "AWD":
            # use average circumreference in this case
            tire_circ_ref = 0.5 * (self.f_circ_ref
                                   + self.r_circ_ref)

        else:
            raise RuntimeError("Powertrain topology unknown!")

        return tire_circ_ref * (1 + (vel * 3.6 - 60.0) * (0.045 / 200.0))

    def r_driven_tire(self, vel: float):
        """Velocity input in m/s. Output is in m."""

        return self.circumref_driven_tire(vel=vel) / (2 * np.pi)

    def calc_tire_degradation(self, tire_age_start: int or float,
                              stint_length: int,
                              compound: str,
                              tire_pars: dict):
        """
        author:
        Alexander Heilmeier

        date:
        18.11.2019

        .. description::
        This function returns a float or an array containing the tire degradation
        time delta(s). The function uses either the math (stint_length == 1) or numpy
        library (stint_length > 1) for best performance.

        linear model: t_tire = k_0 + k_1_lin * age
        quadratic model: t_tire = k_0 + k_1_quad * age + k_2_quad * age**2
        cubic model: t_tire = k_0 + k_1_cub * age + k_2_cub * age**2 + k_3_cub * age**3
        logarithmic model: t_tire = k_0 + k_1_ln * ln(k_2_ln * age + 1)

        .. inputs::
        :param tire_age_start:  tire age in laps at start of current stint
        :type tire_age_start:   int or float
        :param stint_length:    length of current stint
        :type stint_length:     int
        :param compound:        tire compound of current stint
        :type compound:         str
        :param tire_pars:       tire parameters for current driver
        :type tire_pars:        dict

        .. outputs::
        :return t_tire_degr:    tire degradation time delta(s) in seconds
        :rtype t_tire_degr:     np.ndarray or float
        """

        # check input
        if tire_pars["tire_deg_model"] not in ['lin', 'quad', 'cub', 'ln']:
            raise RuntimeError('Unknown tire degradation model!')

        # CASE 1: calculation for a single lap (using math library)
        if stint_length == 1:
            # linear degradation model
            if tire_pars["tire_deg_model"] == 'lin':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_lin'] * tire_age_start)

            # quadratic tire degradation model
            elif tire_pars["tire_deg_model"] == 'quad':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_quad'] * tire_age_start
                               + tire_pars[compound]['k_2_quad']
                               * math.pow(tire_age_start, 2))

            # cubic tire degradation model
            elif tire_pars["tire_deg_model"] == 'cub':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_cub'] * tire_age_start
                               + tire_pars[compound]['k_2_cub']
                               * math.pow(tire_age_start, 2)
                               + tire_pars[compound]['k_3_cub']
                               * math.pow(tire_age_start, 3))

            # logarithmic degradation model
            else:
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_ln']
                               * math.log(tire_pars[compound]['k_2_ln']
                               * tire_age_start + 1.0))

        # CASE 2: calculation for more than one lap (using numpy library)
        else:
            laps_tmp = np.arange(tire_age_start, tire_age_start + stint_length)

            # linear degradation model
            if tire_pars["tire_deg_model"] == 'lin':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_lin'] * laps_tmp)

            # quadratic tire degradation model
            elif tire_pars["tire_deg_model"] == 'quad':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_quad'] * laps_tmp
                               + tire_pars[compound]['k_2_quad'] * np.power(laps_tmp, 2))

            # cubic tire degradation model
            elif tire_pars["tire_deg_model"] == 'cub':
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_quad'] * laps_tmp
                               + tire_pars[compound]['k_2_quad'] * np.power(laps_tmp, 2)
                               + tire_pars[compound]['k_2_quad'] * np.power(laps_tmp, 3))

            # logarithmic degradation model
            else:
                t_tire_degr = (tire_pars[compound]['k_0']
                               + tire_pars[compound]['k_1_ln']
                               * np.log(tire_pars[compound]['k_2_ln'] * laps_tmp + 1.0))

        return t_tire_degr

    def calculate_free_rolling_radius(self, diameter_no_load, width, pressure):
        # Convert width from millimeters to inches
        width_inches = width / 25.4
        # Calculate loaded radius as 97% of the diameter with no load
        loaded_radius = diameter_no_load * 0.485

        # Calculate section height using free rolling radius and tire diameter
        free_rolling_radius = loaded_radius * 0.965  #0.965 deformation factor (no so good for f1) # TODO find a way to reestimate this value
        # TODO convert to named constant for easy reading
        tire_diameter = diameter_no_load * 0.0254  #0.0254 inches to meters factor
        section_height = (tire_diameter - 2 * free_rolling_radius) / 2

        # Calculate aspect ratio using section height and width
        aspect_ratio = (section_height / width_inches) * 100

        # Calculate free rolling radius using loaded radius, pressure, width, and aspect ratio
        free_rolling_radius = loaded_radius + (pressure * width_inches / (2 * aspect_ratio * 100))
        return free_rolling_radius

    def calc_distance(self, speed, Fz, gamma, kappa):
        """
            Calculate the distance traveled by a tire given a speed and various parameters related to the tire and the road.
            Args:
            speed (float): The speed of the tire in meters per second.
            Fz (float): The vertical load on the tire in Newtons.
            gamma (float): The slip angle of the tire in radians.
            kappa (float): The longitudinal slip of the tire.

            Returns:
            float: The distance traveled by the tire in meters.
        """

        # Tire model parameters
        B = 10.0  # Stiffness factor
        C = 1.5  # Shape factor
        D = 2200.0  # Peak value of longitudinal friction coefficient
        E = -0.8  # Curvature factor
        F = 1.0  # Peak value of lateral friction coefficient
        G = 10000.0  # Vertical load factor
        H = 0.0  # Horizontal shift factor
        R0 = 0.3  # Free rolling radius

        # Calculate the vertical force on the tire due to the load.
        Fz0 = Fz * math.cos(gamma)

        # Calculate the tire deformation caused by the vertical force.
        R = R0 * (1.0 - (Fz0 / G))

        # Calculate the longitudinal and lateral forces on the tire.
        BCD = B * C * D
        Fx = BCD * math.sin(C * math.atan((E * kappa) - (F * (E * kappa)) / (BCD)))
        Fy = B * math.sin(C * math.atan(B * gamma - H * (B * gamma)))

        return speed * (
            (R + (Fz0 / (2.0 * B * C))) * (1.0 - ((Fz0 * Fy) / (B * C * G)))
            + (Fz0 * Fx) / (B * C * G)
        )

tireset_pars = {"HAM": {"tire_deg_model": "lin",
                        "mult_tiredeg_sc": 0.25,
                        "mult_tiredeg_fcy": 0.5,
                        "t_add_coldtires": 1.0,
                        "A3": {"k_0": 0.615,
                               "k_1_lin": 0.107,
                               "k_1_quad": 0.125,
                               "k_2_quad": -0.001,
                               "k_1_cub": 0.232,
                               "k_2_cub": -0.017,
                               "k_3_cub": 0.001
                               },
                        "A4": {"k_0": 0.175,
                               "k_1_lin": 0.251,
                               "k_1_quad": 0.546,
                               "k_2_quad": -0.024,
                               "k_1_cub": 0.911,
                               "k_2_cub": -0.089,
                               "k_3_cub": 0.003
                               },
                        "A5": {"k_0": 0.0,
                               "k_1_lin": 0.055,
                               "k_1_quad": -0.017,
                               "k_2_quad": 0.012,
                               "k_1_cub": -0.864,
                               "k_2_cub": 0.323,
                               "k_3_cub": -0.028
                               }
                        }
                }
a = Tires("A3", 0, tireset_pars)
print(a.circumref_driven_tire(40))
print(a.r_driven_tire(60))
# print(a.plot_tire_characteristics())
