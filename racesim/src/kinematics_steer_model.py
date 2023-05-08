from math import atan2, sin, cos, tan


def normalize_angle(angle: float):
    """
    :param angle:       (float) angle [rad]
    :return angle:      (float) angle [rad]
    """
    return lambda angle: atan2(sin(angle), cos(angle))


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

        self.delta_time = delta_time
        self.wheelbase = wheelbase
        self.max_steer = max_steer

    def update(self, x: float, y: float,
               yaw: float, velocity: float,
               acceleration: float,
               steering_angle: float):
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
        acceleration (int) : vehicle's acceleration [m/s^2]
        steering_angle (int) : vehicle's steering angle [rad]
        Returns
        -------
        new_x (int) : vehicle's x-coordinate [m]
        new_y (int) : vehicle's y-coordinate [m]
        new_yaw (int) : vehicle's heading [rad]
        new_velocity (int) : vehicle's velocity in the x-axis [m/s]
        steering_angle (int) : vehicle's steering angle [rad]
        angular_velocity (int) : vehicle's angular velocity [rad/s]
        """
        # Compute the local velocity in the x-axis
        new_velocity = velocity + self.delta_time * acceleration

        # Limit steering angle to physical vehicle limits
        # steering_angle = -self.max_steer if steering_angle < -self.max_steer else self.max_steer if steering_angle > self.max_steer else steering_angle
        steering_angle = (
            -self.max_steer
            if steering_angle < -self.max_steer
            else min(steering_angle, self.max_steer)
        )

        # Compute the angular velocity
        angular_velocity = new_velocity*tan(steering_angle) / self.wheelbase

        # Compute the final state using the discrete time model
        new_x   = x + velocity*cos(yaw)*self.delta_time
        new_y   = y + velocity*sin(yaw)*self.delta_time
        new_yaw = normalize_angle(yaw + angular_velocity*self.delta_time)

        return new_x, new_y, new_yaw, new_velocity, steering_angle,

import numpy as np

class CarDescription:

    def __init__(self, overall_length: float,
                 overall_width: float,
                 rear_overhang: float,
                 tyre_diameter: float,
                 tyre_width: float,
                 axle_track: float,
                 wheelbase: float):

        """
        Description of a car for visualizing vehicle control in Matplotlib.
        All calculations are done w.r.t the vehicle's rear axle to reduce computation steps.

        At initialization
        :param overall_length:          (float) vehicle's overall length [m]
        :param overall_width:           (float) vehicle's overall width [m]
        :param rear_overhang:           (float) distance between the rear bumper and the rear axle [m]
        :param tyre_diameter:           (float) diameter of the vehicle's tyre [m]
        :param tyre_width:              (float) width of the vehicle's tyre [m]
        :param axle_track:              (float) length of the vehicle's axle track [m]
        :param wheelbase:               (float) length of the vehicle's wheelbase [m]

        At every time step
        :param x:                       (float) x-coordinate of the vehicle's rear axle
        :param y:                       (float) y-coordinate of the vehicle's rear axle
        :param yaw:                     (float) vehicle's heading [rad]
        :param steer:                   (float) vehicle's steering angle [rad]

        :return outlines:               (ndarray) vehicle's outlines [x, y]
        :return front_right_wheel:      (ndarray) vehicle's front-right axle [x, y]
        :return rear_right_wheel:       (ndarray) vehicle's rear-right axle [x, y]
        :return front_left_wheel:       (ndarray) vehicle's front-left axle [x, y]
        :return rear_left_wheel:        (ndarray) vehicle's rear-right axle [x, y]
        """

        rear_axle_to_front_bumper  = overall_length - rear_overhang
        centerline_to_wheel_centre = 0.5 * axle_track
        centerline_to_side         = 0.5 * overall_width

        vehicle_vertices = np.array([
            (-rear_overhang,              centerline_to_side),
            ( rear_axle_to_front_bumper,  centerline_to_side),
            ( rear_axle_to_front_bumper, -centerline_to_side),
            (-rear_overhang,             -centerline_to_side)
        ])

        half_tyre_width            = 0.5 * tyre_width
        centerline_to_inwards_rim  = centerline_to_wheel_centre - half_tyre_width
        centerline_to_outwards_rim = centerline_to_wheel_centre + half_tyre_width

        # Rear right wheel vertices
        wheel_vertices = np.array([
            (-tyre_diameter, -centerline_to_inwards_rim),
            ( tyre_diameter, -centerline_to_inwards_rim),
            ( tyre_diameter, -centerline_to_outwards_rim),
            (-tyre_diameter, -centerline_to_outwards_rim)
        ])

        self.outlines         = np.concatenate([vehicle_vertices, [vehicle_vertices[0]]])
        self.rear_right_wheel = np.concatenate([wheel_vertices,   [wheel_vertices[0]]])

        # Reflect the wheel vertices about the x-axis
        self.rear_left_wheel  = self.rear_right_wheel.copy()
        self.rear_left_wheel[:, 1] *= -1

        # Translate the wheel vertices to the front axle
        front_left_wheel  = self.rear_left_wheel.copy()
        front_right_wheel = self.rear_right_wheel.copy()
        front_left_wheel[:, 0]  += wheelbase
        front_right_wheel[:, 0] += wheelbase

        get_face_centre = lambda vertices: np.array([
            0.5*(vertices[0][0] + vertices[2][0]),
            0.5*(vertices[0][1] + vertices[2][1])
        ])

        # Translate front wheels to origin
        self.fr_wheel_centre = get_face_centre(front_right_wheel)
        self.fl_wheel_centre = get_face_centre(front_left_wheel)
        self.fr_wheel_origin = front_right_wheel - self.fr_wheel_centre
        self.fl_wheel_origin = front_left_wheel - self.fl_wheel_centre

        # Class variables
        self.x: float   = None
        self.y: float   = None
        self.yaw_vector = np.empty((2, 2))

    def get_rotation_matrix(_, angle: float) -> np.ndarray:
        """_summary_

        Args:
            _ (_type_): _description_
            angle (float): _description_

        Returns:
            np.ndarray: _description_
        """
        cos_angle = cos(angle)
        sin_angle = sin(angle)

        return np.array([
            ( cos_angle, sin_angle),
            (-sin_angle, cos_angle)
        ])

    def transform(self, point: np.ndarray) -> np.ndarray:
        """_summary_
        Args:
            point (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """
        # Vector rotation
        point = point.dot(self.yaw_vector).T

        # Vector translation
        point[0, :] += self.x
        point[1, :] += self.y

        return point

    def plot_car(self, x: float, y: float, yaw: float, steer: float) :
        """_summary_
        Args:
            x (float): _description_
            y (float): _description_
            yaw (float): _description_
            steer (float): _description_

        Returns:
            tuple[np.ndarray, ...]: _description_
        """
        self.x = x
        self.y = y

        # Rotation matrices
        self.yaw_vector = self.get_rotation_matrix(yaw)
        steer_vector    = self.get_rotation_matrix(steer)

        # Rotate the wheels about its position
        front_right_wheel  = self.fr_wheel_origin.copy()
        front_left_wheel   = self.fl_wheel_origin.copy()
        front_right_wheel  = front_right_wheel@steer_vector
        front_left_wheel   = front_left_wheel@steer_vector
        front_right_wheel += self.fr_wheel_centre
        front_left_wheel  += self.fl_wheel_centre

        outlines          = self.transform(self.outlines)
        rear_right_wheel  = self.transform(self.rear_right_wheel)
        rear_left_wheel   = self.transform(self.rear_left_wheel)
        front_right_wheel = self.transform(front_right_wheel)
        front_left_wheel  = self.transform(front_left_wheel)

        return outlines, front_right_wheel, rear_right_wheel, front_left_wheel, rear_left_wheel

def main():

    from matplotlib import pyplot as plt

    # Based on Tesla's model S 100D (https://www.car.info/en-se/tesla/model-s/model-s-100-kwh-awd-16457112/specs)
    overall_length = 5.4
    overall_width  = 1.6
    tyre_diameter  = 0.720
    tyre_width     = 0.405
    axle_track     = 2.0
    wheelbase      = 3.490
    # TODO wrong assumption : that the distance from axel to rear or front are equals
    rear_overhang  = 0.749
    colour         = 'black'

    # Initial state
    x     =  30.0
    y     = 0.0
    yaw   = 2*np.pi 
    steer = np.deg2rad(25)

    desc = CarDescription(overall_length, overall_width, rear_overhang, tyre_diameter, tyre_width, axle_track, wheelbase)
    desc_plots = desc.plot_car(x, y, yaw, steer)

    ax = plt.axes()
    ax.set_aspect('equal')

    for desc_plot in desc_plots:
        ax.plot(*desc_plot, color=colour)

    plt.show()

if __name__ == '__main__':
    main()

