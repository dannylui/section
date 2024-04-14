import math
import numpy as np

class Archy:

    def __init__(self):

        pass

    # find the radius of the arch if a circle
    def find_radius(self, rise, span):

        return (span^2 + 4 * rise^2)^0.5 / 2

    # Return the chord angle in radians
    def find_chord_angle(self, rise, span):

        r = self.find_radius(rise, span)

        return math.asin(span / (2 * r)) * 2

    # returns x, y coordinates of the circle
    def get_centroid_coord(self, rise, span):

        r = self.find_radius(rise, span)

        return span/2, rise - r


    def get_arch_nodes(self, rise, span, n_segments = 10):

        theta = self.find_chord_angle(rise, span)
        r = self.find_radius(rise, span)
        alpha = (math.pi - theta) / 2

        increment = np.linspace(0, theta, n_segments)
        x = r - r * math.cos(alpha + increment)
        y = r * math.sin(alpha + increment) - (rise - r)

        return x, y






