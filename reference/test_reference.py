import unittest

import numpy as np

from compare import compare
from optics import display_rgb, pinhole, quad_distance, sphere_distance


class CalibrationTests(unittest.TestCase):
    def test_pixel_centers_and_orientation(self):
        eye = np.zeros(3)
        rays = pinhole(eye, [0, 0, -1], [0, 1, 0], 90, 3, 3, range(3))
        np.testing.assert_allclose(rays[1, 1], [0, 0, -1])
        np.testing.assert_allclose(rays[0, 0] / -rays[0, 0, 2], [-2/3, 2/3, -1])

    def test_intersections(self):
        eye = np.zeros(3)
        direction = np.array([[0., 0., -1.], [1., 0., 0.]])
        np.testing.assert_array_equal(sphere_distance(eye, direction, np.array([0, 0, -5]),
                                                      2, 0), [3, np.inf])
        np.testing.assert_array_equal(quad_distance(eye, direction, np.array([-1, -1, -4]),
                                                    [2, 0, 0], [0, 2, 0], 0), [4, np.inf])

    def test_display_and_negative_controls(self):
        np.testing.assert_array_equal(display_rgb(np.array([0, 0.0031308, 0.18, 1]), 1),
                                      [0, 10, 118, 255])
        linear = np.zeros((4, 512, 3))
        linear[:, 250:260] = 0.18
        reference = display_rgb(linear, 1)
        profile = {"size": [512, 4], "patches": [[253, 1, 2, 2]],
                   "landmarks": [[245, 255, 1]]}
        self.assertTrue(compare(reference, reference, profile)[0]["pass"])
        shifted, _ = compare(reference, np.roll(reference, 1, axis=1), profile)
        self.assertLess(shifted["mean_abs_rgb8"], 0.5)
        self.assertFalse(shifted["pass"])
        self.assertFalse(compare(reference, (linear * 255).astype(np.uint8), profile)[0]["pass"])


if __name__ == "__main__":
    unittest.main()
