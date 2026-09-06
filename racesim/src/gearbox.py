from numpy import argmax, all, array


class GearBox(object):

    def __init__(self):
        self.gear = None
        # GEARBOX MODEL
        # i_trans:                      [-] gear ratio
        # n_shift:                      [1/min] shift rpm
        # e_i:                          [-] torsional mass factor
        # eta_g:                        [-] efficiency of gearbox/transmission
        self.n_shift = array([10000.0, 11800.0, 11800.0, 11800.0, 11800.0, 11800.0,
                              11800.0, 13000.0])
        self.i_trans = array([0.04, 0.070, 0.095, 0.117, 0.143, 0.172, 0.190, 0.206])
        self.e_i = array([1.16, 1.11, 1.09, 1.08, 1.08, 1.08, 1.07, 1.07])
        self.eta_g = 0.96
        # TODO add limits constants

    def get_gear(self, vel: float, circumref_driven_tire: float):
        """Velocity input in m/s. Output is the gear used for that
        velocity (zero based) as well as the corresponding engine rev in 1/s.
        """
        vel = abs(vel)
        # print(f"vel={vel}")
        # calculate theoretical engine revs for all the gears
        n_gears = (vel / (circumref_driven_tire * self.i_trans)) * 60  # [1/min]

        # find largest gear below shift revs
        shift_bool = n_gears < self.n_shift

        if all(~shift_bool):
            # if max rev in final gear is reached do not shift up
            gear_ind = self.n_shift.size - 1
        else:
            # find first True value (zero based indexing of gears)
            gear_ind = int(argmax(shift_bool)) + 1
        # if gear_ind >= len(n_gears):
        # print(f"Gear ind over sized {shift_bool}")
        try:
            n_gears[gear_ind]
        except IndexError:
            gear_ind = 7
        return gear_ind, n_gears[gear_ind]

    def get_rpm_from_vel(self, vel: float, circumref_driven_tire: float):
        gear, rpm = self.get_gear(vel, circumref_driven_tire)
        return rpm, gear

    def get_vel_from_gear(self, gear, rpm, circumref_driven_tire):
        return (rpm * circumref_driven_tire * self.i_trans[gear - 1]) / 60

########### TEST ##################
# from pygame.math import Vector2
# gearbox = GearBox()
# v = 51.0  # [m/s]
# gear, rpm = gearbox.get_gear(v, 2.073)
# vel = gearbox.get_vel_from_gear(4,11132.138483802737, 2.073)
# gear, rpm = gearbox.get_gear(v, 2.073)
# print(gear, rpm, v*60*60/1000)
# print(vel)

# max_speed = 100.0
# vel = Vector2(83, 52)
# speed = max(max_speed, min(max_speed, vel.length()))
# print(speed,vel.magnitude())
# vel.scale_to_length(speed)
# print(vel)
