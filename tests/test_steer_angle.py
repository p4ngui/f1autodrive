
class Car:
    STEERING_THRESHOLD = 0.05
    STEERING_SPEED = 7.5

    def __init__(self):
        self.steering = 0.0
        self.commands = (0.0, 0.0)
        self.max_steering = 30.0

    def update_steering_angle(self, dt):
        # self.steering is angle in deg [°]

        if self.commands[1] <= -self.STEERING_THRESHOLD:
            self.steering -= self.STEERING_SPEED * dt
            self.steering = max(self.steering, -self.max_steering)
        elif self.commands[1] >= self.STEERING_THRESHOLD:
            self.steering += self.STEERING_SPEED * dt
            self.steering = min(self.steering, self.max_steering)
        else:
            self.steering = 0.0
        # self.steering = max(-self.max_steering,
        #                     min(self.max_steering, self.steering))

def test_car_steering():
    car = Car()
    dt = 1.0
    # Test turning right
    param_test_car_steering(car, dt, 1.0, 5, 12.5)
    param_test_car_steering(car, dt, 1.0, 29.0, 30)
    # Test turning left
    param_test_car_steering(car, dt, -1.0, -5, -12.5)
    param_test_car_steering(car, dt, -1.0, -29, -30)
    # Test going straight
    param_test_car_steering(car, dt, 0.03, 0, 0)
    param_test_car_steering(car, dt, -0.03, 0, 0)
    param_test_car_steering(car, dt, 0.0, 0, 0)

    # Test turning right beyond the limit
    param_test_car_steering(car, dt*5, 1.0, 0, 30)

    # Test turning left beyond the limit
    param_test_car_steering(car, dt*5, -1.0, 0, -30)

# TODO Rename this here and in `test_car_steering`


def param_test_car_steering(car, dt, command, initial_steer_angle, valid_test_value):
    car.commands = (0.0, command)
    car.steering = initial_steer_angle
    car.update_steering_angle(dt)
    assert car.steering == valid_test_value
