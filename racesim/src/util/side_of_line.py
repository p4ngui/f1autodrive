import numpy as np
from typing import Union

print("side_of_line")


def side_of_line(a: Union[tuple, np.ndarray],
                 b: Union[tuple, np.ndarray],
                 z: Union[tuple, np.ndarray]) -> float:
    """
    author:
    Alexander Heilmeier

    .. description::
    Function determines if a point z is on the left or right side of a line from a to b. It is based on the z component
    orientation of the cross product, see question on
    https://stackoverflow.com/questions/1560492/how-to-tell-whether-a-point-is-to-the-right-or-left-side-of-a-line

    .. inputs::
    :param a:       point coordinates [x, y]
    :type a:        Union[tuple, np.ndarray]
    :param b:       point coordinates [x, y]
    :type b:        Union[tuple, np.ndarray]
    :param z:       point coordinates [x, y]
    :type z:        Union[tuple, np.ndarray]

    .. outputs::
    :return side:   0.0 = on line, 1.0 = left side, -1.0 = right side.
    :rtype side:    float
    """

    return np.sign((b[0] - a[0]) * (z[1] - a[1]) - (b[1] - a[1]) * (z[0] - a[0]))


# testing --------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    pass
