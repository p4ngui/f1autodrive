import pygame
from pygame.math import Vector2
from math import radians, degrees, sin, cos, atan2, tan
from shapely.geometry import LineString
from shapely.geometry.polygon import Point
from racesim.src.constants import ACC, BRAKE, TURN_LEFT, TURN_RIGHT
from racesim.src.constants import PPM, MMTOMETERS
from racesim.src.constants import STEERING_SPEED, STEERING_THRESHOLD
import racesim.src.gearbox
import racesim.src.tires
import os
import numpy as np


def normalize_angle(angle: float):
    """
    :param angle:       (float) angle [rad]
    :return angle:      (float) angle [rad]
    """
    return atan2(sin(angle), cos(angle))


class KinematicBicycleModel:
    """
    Summary
    -------
    This class implements the 2D Kinematic Bicycle Model for vehicle dynamics
    Attributes
    ----------
    dt (float) : discrete time period [s]
    wheelbase (float) : vehicle's wheelbase [m]
    max_steer (float) : vehicle's steering limits [rad]
    Methods
    -------
    __init__(wheelbase: float, max_steer: float, delta_time: float=0.05)
        initializes the class
    update(x, y, yaw, velocity, acceleration, steering_angle)
        updates the vehicle's state using the kinematic bicycle model
    """
    def __init__(self, wheelbase: float, max_steer: float, delta_time: float = 0.05):


        self.wheelbase = wheelbase
        self.max_steer = max_steer

    def update(self, x: float, y: float,
               yaw: float, velocity: float,
               acceleration: float,
               steering_angle: float, delta_time: float):
        """
        Summary
        -------
        Updates the vehicle's state using the kinematic bicycle model
        Parameters
        ----------
        x (float) : vehicle's x-coordinate [m]
        y (float) : vehicle's y-coordinate [m]
        yaw (float) : vehicle's heading [rad]
        velocity (float) : vehicle's velocity in the x-axis [m/s]
        acceleration (float) : vehicle's acceleration [m/s^2]
        steering_angle (float) : vehicle's steering angle [rad]
        Returns
        -------
        new_x (float) : vehicle's x-coordinate [m]
        new_y (float) : vehicle's y-coordinate [m]
        new_yaw (float) : vehicle's heading [rad]
        new_velocity (float) : vehicle's velocity in the x-axis [m/s]
        steering_angle (float) : vehicle's steering angle [rad]
        angular_velocity (float) : vehicle's angular velocity [rad/s]
        """
        # Compute the local velocity in the x-axis
        new_velocity = velocity + (delta_time * acceleration)

        # Limit steering angle to physical vehicle limits
        # steering_angle = -self.max_steer if steering_angle < -self.max_steer else self.max_steer
        # if steering_angle > self.max_steer else steering_angle
        steering_angle = (
            -self.max_steer
            if steering_angle < -self.max_steer
            else min(steering_angle, self.max_steer)
        )

        # Compute the angular velocity
        angular_velocity = new_velocity*tan(steering_angle) / self.wheelbase

        # Compute the final state using the discrete time model
        new_x = x + velocity*cos(yaw)*delta_time
        new_y = y + velocity*sin(yaw)*delta_time
        new_yaw = normalize_angle(yaw + angular_velocity*delta_time)
        return new_x, new_y, new_yaw, new_velocity, steering_angle,


"""
        https://formulapedia.com/f1-car-length/
        F1 2023 measures in mm
       Team	        Length (m)	Width (m)	Height (m)
        Red Bull	5.4	        2.0	        0.95
        Ferrari	    5.5	        2.0	        0.97
        Mercedes	5.5     	2.0	        0.97
        Alpine	    5.5	        2.0	        1.1
        McLaren	    5.4	        2.0	        0.95
        Alfa Romeo	5.5	        2.0	        0.95
        AstonMartin 5.5	        2.0 	    0.95
        Haas	    5.5	        2.0	        0.95
        AlphaTauri	5.5	        2.0	        0.95
        Williams	5.4	        2.0	        0.96
    """


class Car(pygame.sprite.Sprite):

    def __init__(self, x, y,
                 yaw=0.0,
                 velocity=Vector2(0.0, 0.0),
                 acceleration=0,
                 total_length=5.4,
                 total_width=2.0,
                 max_steer=30,
                 team="Mercedes",
                 driver="HAM"):

        pygame.sprite.Sprite.__init__(self)
        self.images_path = os.path.join(os.path.dirname(__file__), "img")
        self.image = self.loadImage()
        self.orig_image = self.image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        # TODO to rework: fix origin in the nose of the car
        self.position = Vector2(x, y)
        self.rect.center = self.position
        self.pilot_ia = None
        self.genome = None
        self.track_offset_x = None
        self.track_offset_y = None
        # ======= CAR DIMENSIONS
        self.width = total_width * PPM
        self.length = total_length * PPM
        self.axel_track = total_width * PPM
        # reglamentary F1 2020 axes max distance §3.2.2 FIA
        #  McLaren	    5400	2000	950  600:2000 (3.3mm/px), 1405:5400(3.29263mm/px)
        #                  measures from jpg  350:1410 px
        # 1405px:5400mm
        # 302px  195px
        # 1160.71mm    3489.82mm 749.47mm
        # (0,0) front of car                   pivot point    (-5.4,0)
        #   |   Front     |                         |    Rear    |
        #   |<-- 1161 --->|<---------- 3490 ------->|<-- 749 --->| mm
        #   |___________(_|_)_____________________(_|_)__________|
        self.rear_wheel_to_rear_bumper = 749.47 * MMTOMETERS * PPM
        self.front_wheel_to_front_bumper = 1161.71 * MMTOMETERS * PPM
        self.wheel_base = self.length - (
            self.rear_wheel_to_rear_bumper + self.front_wheel_to_front_bumper)
        self.wheel_rear_axe_center = Vector2(-(self.length - self.rear_wheel_to_rear_bumper),
                                             self.width/2)
        self.wheel_front_axe_center = Vector2(-self.front_wheel_to_front_bumper,
                                              self.width/2)

        self.center = Vector2(self.length/2, self.width/2)

        self.cog = None
        # ======= Mass in Kg
        self.mass_gravity = None
        self.weight_empty_kg = 794.0
        self.weight_fuel_kg = 110.0
        self.weight_pilot_kg = 80.0
        self.total_weight_kg = self.weight_empty_kg + self.weight_fuel_kg + self.weight_pilot_kg
        # ======= CAR SETUP
        self.sensor_front_distance = 120.0 * PPM   # 120.0 m
        self.sensor_lateral_distance = 50.0 * PPM  # 50.0  m
        # ======= PERFORMANCE ======
        # TODO load car profiles & calculate limits dynamically
        self.max_acceleration: float = 19.61 * PPM  # 19.61 m/s2 = 2G of acceleration
        self.max_steer: float = max_steer  # [deg]
        self.max_speed = 102.88 * PPM  # (1028px/s => 102.8m/s = 370km/h)
        # TODO Dynamic 5.7G =55,9 m/s2 from real data in 2020
        # TODOupdate date to 2023
        self.brake_deceleration = 55.9 * PPM  # [m/s-2]
        # TODO self.free_deceleration integrate dynamically
        # calculated w/drag coef in function of speed
        self.free_deceleration = 1.0 * PPM  # [m/s-2]
        self.yaw = yaw  # Car direction angle in °
        self.velocity = velocity
        self.angular_velocity: float = 0.0
        # ======= Live data =======
        self.actions = [0.0, 0.0]  # [0.0, 0.0, 0.0, 0.0]
        self.acceleration: float = acceleration
        self.steering: float = 0.0  # in [°] degrees
        self.camera: Vector2 = Vector2(0, 0)  # Assigned the camera as an attribute.
        self.lap_start_time: float = 0.0
        self.laptimes = []
        self.lap_number: int = 0
        self.lap_distance: float = 0.0
        self.velocity.x = min(self.velocity.x, self.max_speed)
        # TODO verify if acceleration is lower or = to max accel
        self.kinematics = KinematicBicycleModel(self.max_steering)
        self.is_out: bool = False
        self.car_no: int = None
        self.sensors = []
        self.inputs = []
        # TODO initialise this vas from game
        # HINT: parameters are per team, not manufacturer!
        # drivetype:                [-] combustion or electric (hybrid is treated as combustion)
        # manufacturer:             [-] manufacturer
        # t_car:                    [s] time loss per lap due to car abilities
        # m_fuel:                   [kg] fuel mass at start (combustion -> set null otherwise)
        # b_fuel_per_lap:           [kg/lap] fuel mass consumption per lap (combustion -> set null
        #                           otherwise)
        # energy:                   [kWh] energy at start (electric -> set null otherwise)
        # energy_per_lap:           [kWh/lap] energy consumption per lap (electric -> set null
        #                               otherwise)
        # mult_consumption_sc:      [-] multiplier for the fuel/energy consumption under an SC
        #                               phase (range[0,1])
        # mult_consumption_fcy:     [-] multiplier for the fuel/energy consumption under an FCY
        #                               phase (range[0,1])
        # auto_consumption_adjust:  [-] automatic adjustment of fuel/energy consumption such that
        #                               car runs out of fuel at the
        #                           end of the race, increases consumption after FCY phases (cannot
        #                           decrease consumption!)
        # t_pit_tirechange_add:     [s] team-specific additional standstill time to change tires
        # t_pit_refuel_perkg:       [s/kg] time per fuel added in pit (set null if there is no
        #                                  refueling) (combustion)
        # t_pit_charge_perkwh:      [s/kWh] time per kWh energy added in pit (set null if there is
        #                                   no recharging) (electric)
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
        # self.gear = self.gearbox.find_gear(self.velocity.length(),
        #                                    self.tires.circumref_driven_tire(
        #                                        self.velocity.length()))

    def set_ia(self, net):
        self.pilot_ia = net

    def set_genome(self, g):
        self.genome = g

    def set_velocity(self, new_velocity):
        self.velocity.x = max(0, min(self.max_speed,
                                     new_velocity))

    def set_track_offset(self, x, y) -> None:
        self.track_offset_x = x
        self.track_offset_y = y

    def get_car_pos(self):
        return Vector2(self.position.x + self.track_offset_x,
                       self.position.y + self.track_offset_y)

    def get_nose_coords(self):
        return Vector2(self.position.x + (self.length * 0.5) + self.track_offset_x,
                       self.position.y + (self.length * 0.5) + self.track_offset_y)

    def get_rear_axel_center_coords(self):
        return Vector2(
            self.position.x - (self.length * 0.5
                               ) + self.rear_wheel_to_rear_bumper + self.track_offset_x,
            self.position.y - (self.length * 0.5
                               ) + self.rear_wheel_to_rear_bumper + self.track_offset_y)

    def get_normal_velocity(self):
        return self.velocity.x/self.max_speed

    def get_center_from_rear_axel_coords(self, rear_x, rear_y):
        center_x = rear_x + (self.length * 0.5) - self.rear_wheel_to_rear_bumper + self.track_offset_x
        center_y = rear_y + (self.length * 0.5) - self.rear_wheel_to_rear_bumper + self.track_offset_y
        return center_x, center_y

    def gen_ia_actions(self, track_left_line: LineString, track_right_line: LineString):
        self.update_sensors()
        self.gen_inputs(track_left_line, track_right_line)
        # inp = [1 - self.inputs[i] for i in range(len(self.inputs)-1)]
        # inp.append(self.inputs[5])
        self.actions = self.pilot_ia.activate(self.inputs)
        # return self.pilot_ia.activate(inputs)

    def gen_inputs(self, track_left_line: LineString, track_right_line: LineString):
        self.inputs = []
        car_pos = Point(self.get_car_pos())
        for m, sensor in enumerate(self.sensors):
            left_intersection_points = track_left_line.intersection(sensor)
            right_intersection_points = track_right_line.intersection(sensor)
            dl = self.distance_to_track(sensor, left_intersection_points, car_pos,
                                        self.sensor_front_distance, self.sensor_lateral_distance, m)
            dr = self.distance_to_track(sensor, right_intersection_points, car_pos,
                                        self.sensor_front_distance, self.sensor_lateral_distance, m)
            self.inputs.append(min(dl, dr))
        self.inputs[0] = 1 - (self.inputs[0] / self.sensor_lateral_distance)
        self.inputs[4] = 1 - (self.inputs[4] / self.sensor_lateral_distance)
        self.inputs[1] = 1 - (self.inputs[1] / self.sensor_lateral_distance)
        self.inputs[3] = 1 - (self.inputs[3] / self.sensor_lateral_distance)
        self.inputs[2] = 1 - (self.inputs[2] / self.sensor_front_distance)
        self.inputs.append(self.get_normal_velocity())

    def distance_to_track(self, sensor,
                          intersection_points,
                          o_pt,
                          sensor_front_distance,
                          sensor_lateral_distance,
                          m):
        if intersection_points.geom_type == "MultiPoint":
            a = {o_pt.distance(pt): pt for pt in intersection_points.geoms}
            intersection_points = a[min(a.keys())]
        if not intersection_points.is_empty:
            return sensor.project(intersection_points)
        else:
            return sensor_lateral_distance if m in [0, 1, 3, 4] else sensor_front_distance

    def update_sensors(self):
        cur_pos = self.get_nose_coords()
        self.sensors = []
        count = 180
        for i in np.arange(4, -1, -1):
            dist = self.sensor_front_distance if i == 2 else self.sensor_lateral_distance
            omega = -radians(self.angle + count - 180)
            count -= 60 if i in [4, 1] else 30
            dx = dist * sin(omega)
            dy = - dist * cos(omega)
            self.sensors.append(
                LineString(
                    [(cur_pos.x,
                      cur_pos.y),
                     (cur_pos.x + dx,
                      cur_pos.y + dy)
                     ]))
        # return sensors

    def detect_collision(self, mask, offset_x, offset_y):
        rect = self.mask.get_rect()
        mask_nb_bits_overlap = mask.overlap_mask(
            self.mask, (int(offset_x + self.position.x - rect.center[0]),
                        int(offset_y + self.position.y - rect.center[1])
                        )).count()

        return ((self.mask.count() - mask_nb_bits_overlap) > 50)

    def loadImage(self):
        # TODO : add random load on create or a color type by tag parameter
        image = pygame.Surface((57, 20), pygame.SRCALPHA)
        image = pygame.transform.rotate(pygame.transform.scale(
            pygame.image.load(os.path.join(self.images_path, 'F1_black_s.png')
                              ).convert_alpha(), (57, 20)), 0)
        return image

    def update_velocity(self, new_velocity: float):
        # self.velocity.x = max(-self.max_speed, min(new_velocity, self.max_speed))
        self.velocity.x = max(0, min(new_velocity, self.max_speed))
        # self.velocity.x = max(self.new_velocity, 0)

    def update_acceleration(self, dt, action):
        threshold = 0.05
        if action <= -threshold:  # from -1.0 to -threshold ==> BRAKE
            self.acceleration = (-self.brake_deceleration
                                 if abs(self.velocity.x) > dt * self.brake_deceleration
                                 else -self.velocity.x / dt)
        elif action >= threshold:  # from threshold to 1.0 ==> ACCELERATE
            # self.acceleration = (72.0927 * np.log(118.4362*action - 33.5337) - 124.974)*dt
            self.acceleration += 1 * dt
            self.acceleration = max(-self.max_acceleration,
                                    min(self.max_acceleration, self.acceleration))
        else:
            self.acceleration = -self.free_deceleration

    def update_camera(self, dt):
        pass

    def update_steering_angle(self, dt):
        # self.steering is angel in deg [°] deg        
        threshold = 0.05
        # Steering left
        if self.actions[1] <= -threshold:
            self.steering -= STEERING_SPEED * dt
            self.steering = max(self.steering, -self.max_steering)
        # Steering right
        elif self.actions[1] >= threshold:
            self.steering += STEERING_SPEED * dt
            self.steering = min(self.steering, self.max_steering)
        # else:
        #     self.steering = 0.0
        # if steer angle is between -1 and 1 steering wheel is centred
        if self.steering > -1 and self.steering < 1:
            self.steering = 0.0
        # # Limit steering angle to physical vehicle limits
        # self.steering = max(-self.max_steering,
        #                     min(self.max_steering, self.steering))

    def update_angular_velocity(self):
        if self.steering:
            turning_radius = self.wheel_base / sin(radians(self.steering))
            self.angular_velocity = self.velocity.x / turning_radius
        else:
            self.angular_velocity = 0

    def update_fitness(self, add_to_fitness):
        self.genome.fitness += add_to_fitness

    def update(self, dt):
        # TODO change Acceleration by throttle
        # add model to convert throttle in acceleration
        # find right gear (add delay to get the right gear)
        # and accelerate according throttle position
        # and power delivered by engine + gearbox + road grip coef
        # to the Tyre with Tyre group surface ....
        # TODO idem for brake output will be brake position
        # add model to transform brake pedal position into
        # brake force according driver force, driver fitness
        # and brake force of the car
        # TODO add model of acceleration / brake change
        rac = self.get_rear_axel_center_coords()
        self.update_steering_angle(dt)
        self.update_acceleration(dt, self.actions[0])
        (rear_wheel_axel_center_x,
         rear_wheel_axel_center_y,
         new_yaw, new_velocity,
         new_steering_angle,
         new_angular_velocity) = self.kinematics.update(rac.x,
                                                        rac.y,
                                                        self.yaw,
                                                        self.velocity.x,
                                                        self.acceleration,
                                                        degrees(self.steering),
                                                        dt)

        self.update_velocity(new_velocity)
        # TODO rename lap_distance by traveled_distance
        self.lap_distance += self.velocity.x * dt / 1000
        self.update_angular_velocity()
        vel = self.velocity.rotate(-self.angle) * dt
        self.position += vel
        self.camera += vel  # Update the camera position as well.
        self.angle += degrees(self.angular_velocity) * dt
        # If you use the rect as the blit position, you should update it, too.
        self.rect.center = self.position

        self.image = pygame.transform.rotozoom(self.orig_image,
                                               self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        # game.car_group.rect = self.image.get_rect(center=self.rect.center)
        return (self.position.x, self.position.y)

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
