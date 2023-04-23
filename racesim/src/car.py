import pygame
from pygame.math import Vector2
from math import radians, degrees, sin, cos
from shapely.geometry import LineString
from racesim.src.constants import ACC, BRAKE, STEER, THROTTLE, TURN_LEFT, TURN_RIGHT
import racesim.src.gearbox
import racesim.src.tires
import os
import numpy as np
    """
        https://formulapedia.com/f1-car-length/
        F1 2023 messures in mm
                    Length  width   height
        Mercedes	5500	2000	970
        Red Bull	5400	2000	950
        Ferrari	    5500	2000	970
        Alpine	    5620	2000	1100
        McLaren	    5400	2000	950  600:2000 (3.3mm/px), 1640:5400(3.29263mm/px)
                       mesures from jpg  350:1410px 1165:4700 mm
        Alfa Romeo	5500	2000	950
        Haas	    5500	2000	950
        Alpha Tauri	5500	2000	950
        Aston Martin5600	2000	950
        Williams	5400	2000	960
    """

class Car(pygame.sprite.Sprite):

    def __init__(self, x, y,
                 angle=0.0,
                 velocity=Vector2(0.1, 0.1),
                 acceleration=0,
                 length=54,
                 width=20,
                 max_steering=30,
                 max_acceleration=5.0,
                 team="Mercedes",
                 driver="HAM"):

        pygame.sprite.Sprite.__init__(self)
        self.images_path = os.path.join(os.path.dirname(__file__), "img")
        self.image = self.loadImage()
        self.orig_image = self.image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        self.position = Vector2(x, y)
        self.rect.center = self.position

        self.angle = angle
        self.velocity = velocity

        # ======= CAR DIMENTIONS
        self.width = width
        self.length = length
        # regalmentary F1 2020 axes max distnce §3.2.2 FIA
        #  McLaren	    5400	2000	950  600:2000 (3.3mm/px), 1405:5400(3.29263mm/px)
        #                  mesures from jpg  350:1410 px
        #1405px:5400mm
        # 302px  195px
        # 1160.71mm    3489.82mm 749.47mm
        #   |   Front                                   Rear    |
        #   |<-- 1161 --->| <--------- 3490 ------->|<-- 749 --->| mm
        #   |___________(_|_)_____________________(_|_)__________|
        self.wheel_rear_axe_center = Vector2(8.10, self.width/2)
        self.wheel_front_axe_center = Vector2(self.length - 12.25, self.width/2)
        self.wheel_axe_distance = self.length - (11.5244 + 7.5732)
        self.center = Vector2(self.length/2, self.width/2)
        self.gravity_center = None
        self.mass_gravity = None
        self.weight_empty_kg = None
        self.width_fuel_kg = None
        self.weight_pilot_kg = None

        # ======= CAR SETUP
        self.sensor_front_distance = 1200
        self.sensor_lateral_distance = 500
        # ======= PERFORMANCE ======
        # TODO load car profiles & calculate limits dynamically
        self.max_acceleration = 196.1  # 19.61 m/s2 = 2G of acceleration
        self.max_steering = max_steering  # [deg]
        self.max_speed = 1028  # (1028px/s => 102.8m/s = 370km/h)
        # TODO Dynamic 5.7G =55,9 m/s2 from real data in 2020
        self.brake_deceleration = 559  # [px/s-2]
        # TODO self.free_deceleration integrate dynamically
        # calculated w/drag coef in fonction of speed
        self.free_deceleration = 10  # [px/s-2]
        # ======= Live data =======
        self.commands = [0, 0]  # [0, 0, 0, 0]
        self.acceleration = acceleration
        self.steering = 0.0
        self.camera = Vector2(0, 0)  # Assigned the camera as an attribute.
        self.lap_start_time = 0.0
        self.laptimes = []
        self.lap_number = 1
        self.lap_distance = 0.0
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        # TODO verify if acceleration is lower or = to max accel
        self.is_out = False
        self.car_no = None
        # TODO initialise this vas from game
        # HINT: parameters are per team, not manufacturer!
        # drivetype:                [-] combustion or electric (hybrid is treated as combustion)
        # manufacturer:             [-] manufacturer
        # t_car:                    [s] time loss per lap due to car abilities
        # m_fuel:                   [kg] fuel mass at start (combustion -> set null otherwise)
        # b_fuel_perlap:            [kg/lap] fuel mass consumption per lap (combustion -> set null otherwise)
        # energy:                   [kWh] energy at start (electric -> set null otherwise)
        # energy_perlap:            [kWh/lap] energy consumption per lap (electric -> set null otherwise)
        # mult_consumption_sc:      [-] multiplier for the fuel/energy consumption under an SC phase (range[0,1])
        # mult_consumption_fcy:     [-] multiplier for the fuel/energy consumption under an FCY phase (range[0,1])
        # auto_consumption_adjust:  [-] automatic adjustment of fuel/energy consumption such that car runs out of fuel at the
        #                           end of the race, increases consumption after FCY phases (cannot decrease consumption!)
        # t_pit_tirechange_add:     [s] team-specific additional standstill time to change tires
        # t_pit_refuel_perkg:       [s/kg] time per fuel added in pit (set null if there is no refueling) (combustion)
        # t_pit_charge_perkwh:      [s/kWh] time per kWh energy added in pit (set null if there is no recharging) (electric)
        # color:                    [-] hex color code of the team for plotting
        self.car_pars = {"Mercedes":
                         {"drivetype": "combustion",
                          "manufacturer": "Mercedes",
                          "t_car": 0.0,
                          "m_fuel": 100.0,
                          "b_fuel_perlap": 1.782,
                          "energy": None,
                          "energy_perlap": None,
                          "mult_consumption_sc": 0.25,
                          "mult_consumption_fcy": 0.5,
                          "auto_consumption_adjust": True,
                          "t_pit_tirechange_add": 0.434,
                          "t_pit_refuel_perkg": None,
                          "t_pit_charge_perkwh": None,
                          "color": "#00D2BE",
                          "driver": {"HAM":
                                     {"tire_deg_model": "lin",
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
                          }
                         }
        # tire_deg_model:           [-] tire degradation model -> lin (linear), ln (logarithmic), quad (quadratic), cub (cubic)
        # mult_tiredeg_sc:          [-] multiplier for the tire degradation under an SC phase (range[0,1])
        # mult_tiredeg_fcy:         [-] multiplier for the tire degradation under an FCY phase (range[0,1])
        # t_add_coldtires:          [s] time loss due to a cold (i.e. pre-heated) tire
        # k_0:                      [s] tire degradation parameter -> time offset of tire compound for fresh tires
        # k_1_lin:                  [s/lap] tire degradation parameter (linear model)
        # k_1_quad:                 [s/lap] tire degradation parameter (quadratic model)
        # k_2_quad:                 [s/lap^2] tire degradation parameter (quadratic model)
        # k_1_cub:                  [s/lap] tire degradation parameter (cubic model)
        # k_2_cub:                  [s/lap^2] tire degradation parameter (cubic model)
        # k_3_cub:                  [s/lap^3] tire degradation parameter (cubic model)
        # k_1_ln:                   [?] tire degradation parameter (logarithmic model)
        # k_2_ln:                   [?] tire degradation parameter (logarithmic model) -> scaling of age
        self.tireset_pars = self.car_pars[team]['driver'][driver]

        self.tires = racesim.src.tires.Tires("A3", 0, self.car_pars[team]['driver'][driver])
        self.gearbox = racesim.src.gearbox.GearBox()
        self.gear = self.gearbox.find_gear(self.velocity.length(),
                                           self.tires.circumref_driven_tire(
                                               self.velocity.length()))

    def loadImage(self):
        # TODO : add random load on create or a color type by tag parameter
        image = pygame.Surface((57, 20), pygame.SRCALPHA)
        image = pygame.transform.rotate(pygame.transform.scale(
            pygame.image.load(os.path.join(self.images_path, 'F1_black_s.png')
                              ).convert_alpha(), (57, 20)), 0)
        return image

    def getSensors(self, cur_pos):
        sensors = []
        count = 180
        for i in np.arange(4, -1, -1):
            dist = self.sensor_front_distance if i == 2 else self.sensor_lateral_distance
            omega = -radians(self.angle + count - 180)
            count -= 60 if i in [4, 1] else 30
            dx = dist * sin(omega)
            dy = - dist * cos(omega)
            sensors.append(
                LineString(
                    [(cur_pos.x,
                      cur_pos.y),
                     (cur_pos.x + dx,
                      cur_pos.y + dy)
                     ]))
        return sensors

    def update_velocity(self,dt):

        """dt (float) : discrete time period [s]
        wheelbase (float) : vehicle's wheelbase [m]
        max_steer (float) : vehicle's steering limits [rad]
        """

        """
        Summary
        -------
        Updates the vehicle's state using the kinematic bicycle model
        Parameters
        ----------
        x (int) : vehicle's x-coordinate [m]
        y (int) : vehicle's y-coordinate [m]
        yaw (int) : vehicle's heading [rad]
        velocity (int) : vehicle's velocity in the x-axis [m/s]
        acceleration (int) : vehicle's accleration [m/s^2]
        steering_angle (int) : vehicle's steering angle [rad]
        Returns
        -------
        new_x (int) : vehicle's x-coordinate [m]
        new_y (int) : vehicle's y-coordinate [m]
        new_yaw (int) : vehicle's heading [rad]
        new_velocity (int) : vehicle's velocity in the x-axis [m/s]
        steering_angle (int) : vehicle's steering angle [rad]
        angular_velocity (int) : vehicle's angular velocity [rad/s]
        # Compute the local velocity in the x-axis
        new_velocity = velocity + self.delta_time * acceleration
        """
        new_velocity = velocity + self.delta_time * acceleration
        # Compute the angular velocity
        angular_velocity = new_velocity*tan(steering_angle) / self.wheelbase

    def update_acceleration(self,dt):
        
    def update_position(self,dt):
        # Compute the final state using the discrete time model
        new_x   = x + velocity*cos(yaw)*self.delta_time
        new_y   = y + velocity*sin(yaw)*self.delta_time
        new_yaw = normalise_angle(yaw + angular_velocity*self.delta_time)
    def update_camera(self,dt):
        
    def update_steering_angle(self,dt):
        # Limit steering angle to physical vehicle limits
        steering_angle = -self.max_steer if steering_angle < -self.max_steer else self.max_steer if steering_angle > self.max_steer else steering_angle

    def update(self, dt):
        self.velocity.scale_to_length(max(self.velocity.length() + 1 * self.acceleration * dt, 10e-1))
        # max(min(maxn, n), minn)
        if self.velocity.length() > 0:
            self.velocity.scale_to_length(max(10e-1, min(self.max_speed, self.velocity.length())))
        else:
            self.velocity = Vector2(10e-1, 10e-1)
        self.lap_distance += self.velocity.length() * dt / 1000
        if self.steering:
            turning_radius = self.wheel_axe_distance / sin(radians(self.steering))
            angular_velocity = self.velocity.length() / turning_radius
        else:
            angular_velocity = 0
        self.angle += degrees(angular_velocity) * dt
        vel = self.velocity.rotate(-self.angle)
        self.position += vel
        self.camera += vel  # Update the camera position as well.
        # If you use the rect as the blit position, you should update it, too.
        self.rect.center = self.position

        self.image = pygame.transform.rotozoom(self.orig_image,
                                               self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        # game.car_group.rect = self.image.get_rect(center=self.rect.center)
        return (self.position.x, self.position.y)

    def move(self, dt):
        # TODO change Acceleration by trothle
        # add model to convert trottle in acceleration
        # find rigth gear (add delay to get the right gear)
        # and accelerate according throtle possition
        # and power delivered by engine + gearbox + road grip coef
        # to the tyre with tyre grup surfase ....
        # TODO idem for braek outpul will be brake possition
        # add model to tranform brake pedal position into
        # brake force according driver force, driver fitness
        # and brake force of the car
        # TODO add model of acceleration / brake change
        if self.commands[0] <= -0.33:  # from -1.0 to -0.66 ==> BRAKE
            self.acceleration = (-self.brake_deceleration
                                 if abs(self.velocity.length()) > dt * self.brake_deceleration
                                 else -self.velocity.length() / dt
                                 )
        elif self.commands[0] >= 0.33:  # from -0.33 to 1.0 ==> ACCELERATE
            self.acceleration += 10 * dt
            self.acceleration = max(-self.max_acceleration,
                                    min(self.max_acceleration, self.acceleration))
        else:
            # if dt != 0:
            # if abs(self.velocity.length()) > dt * self.free_deceleration:
            self.acceleration = -self.free_deceleration
            # self.acceleration = -self.velocity.length() / dt
            # self.acceleration = max(-self.max_acceleration,
            #                         min(self.acceleration, self.max_acceleration)
            # )
        if self.commands[1] <= -0.33:  # from -1.0 to -0.66 ==> TURN RIGHT
            self.steering -= 7.5 * dt
        elif self.commands[1] >= 0.33:  # from -0.33 to 1.0 ==> TURN LEFT
            self.steering += 7.5 * dt
        else:  # from -0.67 to -0.33 ==> Go STRAIGHT
            self.steering = 0

        # if decodeCommand(self.commands, ACC):
        #     # if self.velocity.length() < 0:
        #     #     self.acceleration = self.brake_deceleration
        #     # else:
        #     self.acceleration += 1 * dt
        #     self.acceleration = max(-self.max_acceleration,
        #                             min(self.max_acceleration, self.acceleration))
        #         # TODO add model of accelartion change
        # elif decodeCommand(self.commands, BRAKE):
        #     if abs(self.velocity.length()) > dt * self.brake_deceleration:
        #         self.acceleration = -self.brake_deceleration
        #     else:
        #         self.acceleration = -self.velocity.length() / dt
        # else:
        #     if abs(self.velocity.length()) > dt * self.free_deceleration:
        #         self.acceleration = -self.free_deceleration
        #     else:
        #         if dt != 0:
        #             self.acceleration = -self.velocity.length() / dt
        #             self.acceleration = max(-self.max_acceleration,
        #                                     min(self.acceleration,
        #                                         self.max_acceleration))
        # if decodeCommand(self.commands, TURN_RIGHT):
        #     self.steering -= 7.5 * dt
        # elif decodeCommand(self.commands, TURN_LEFT):
        #     self.steering += 7.5 * dt
        # else:
        #     self.steering = 0
        # if self.decodeCommand(self.commands, TURN_RIGHT
        #                  ) or decodeCommand(self.commands, TURN_LEFT):
        #     self.steering = max(-self.max_steering, min(self.steering,
        #                                                 self.max_steering))

    # def decodeCommand(self, commands, type):
    #     if type == ACC and commands[type] >= 0.5 and commands[type] > commands[BRAKE]:
    #         return True
    #     elif type == BRAKE and commands[type] >= 0.5 and commands[type] > commands[ACC]:
    #         return True
    #     elif type == TURN_LEFT and commands[type] >= 0.5 and commands[type] > commands[
    #             TURN_RIGHT]:
    #         return True
    #     elif type == TURN_RIGHT and commands[type] >= 0.5 and commands[type] > commands[
    #             TURN_LEFT]:
    #         return True
    #     return False

    def change_tires(self, compound: str, age: int, tireset_pars: dict):
        """
        Calculate additional laptime due to tireset, i.e. degradation and cold tires. Tire parameters must be handed
        over because they are dependent of the driver.
        """
        # TODO
        return self.tireset_pars["t_add_coldtires"]

    def cond(self):
        # ==================================
        #  Parameters
        # ==================================
        # Throttle to engine torque
        self.a_0 = 400
        self.a_1 = 0.1
        self.a_2 = -0.0002

        # Gear ratio, effective radius, mass + inertia
        self.GR = 0.35
        self.r_e = 0.3
        self.J_e = 10
        self.m = 2000
        self.g = 9.81

        # Aerodynamic and friction coefficients
        self.c_a = 1.36
        self.c_r1 = 0.01

        # Tire force
        self.c = 10000
        self.F_max = 10000

        # State variables
        self.x = 0
        self.v = 5
        self.a = 0
        self.w_e = 100
        self.w_e_dot = 0

        self.sample_time = 0.01

    def reset(self):
        # reset state variables
        self.x = 0
        self.v = 5
        self.a = 0
        self.w_e = 100
        self.w_e_dot = 0

    def t_to_v(self, throttle, alpha, dt):
        # ==================================
        #  Implement vehicle model here
        # ==================================
        F_aero = self.c_a * self.v * self.v
        R_x = self.c_r1 * self.v
        F_g = self.m * self.g * np.sin(alpha)
        F_load = F_aero + R_x + F_g
        T_e = throttle * (self.a_0 + self.a_1 * self.w_e + self.a_2 * self.w_e * self.w_e)
        W_w = self.GR * self.w_e
        r_eff = self.v / W_w
        s = (W_w * self.r_e - self.v) / self.v
        cs = self.c * s
        F_x = cs if abs(s) < 1 else self.F_max
        self.x = self.x + self.v * self.sample_time
        self.v = self.v + self.a * self.sample_time
        self.a = (F_x - F_load) / self.m
        self.w_e = self.w_e + self.w_e_dot * self.sample_time
        self.w_e_dot = (T_e - self.GR * self.r_e * F_load) / self.J_e


def decodeCommand(commands, type):
    if type == ACC and commands[type] >= 0.50 and commands[type] > commands[BRAKE]:
        return True
    elif type == BRAKE and commands[type] >= 0.5 and commands[type] > commands[ACC]:
        return True
    elif type == TURN_LEFT and commands[type] >= 0.5 and commands[type] > commands[
            TURN_RIGHT]:
        return True
    elif type == TURN_RIGHT and commands[type] >= 0.5 and commands[type] > commands[
            TURN_LEFT]:
        return True
    return False
