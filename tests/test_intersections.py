# from pygame.math import Vector2
from shapely.geometry import LineString
# from shapely.geometry.polygon import Point
from racesim.src.car import Car

if __name__ == "__main__":
    from functools import partial
    from timeit import timeit
    car = Car(-0,-0)
    track_left_line = LineString([(1, 0), (1, 0)])
    track_right_line = LineString([(0, 1), (0, 1)])
    print(timeit(partial(car.get_inputs,track_left_line, track_right_line),number=500000))
    print(timeit(partial(car.get_inputs2,track_left_line, track_right_line),number=500000))
    