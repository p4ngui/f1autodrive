
class SteeringObject:

    def __init__(self, max_steering, steering):
        self.max_steering = max_steering
        self.steering = max(-self.max_steering,
                            min(self.max_steering, steering))


# @pytest.mark.parametrize("steering", range(-31, 31))
def test_steering():
    test_object_1 = SteeringObject(max_steering=30, steering=-50)
    assert test_object_1.steering == -30

    test_object_2 = SteeringObject(max_steering=30, steering=40)
    assert test_object_2.steering == 30

    test_object_3 = SteeringObject(max_steering=30, steering=0)
    assert test_object_3.steering == 0

    test_object_4 = SteeringObject(max_steering=30, steering=-10)
    assert test_object_4.steering == -10

    test_object_5 = SteeringObject(max_steering=30, steering=15)
    assert test_object_5.steering == 15
