"""
This test is modified from: https://gist.github.com/dennis-tra/994a65d6165a328d4eabaadbaedac2cc

Author: dennis-tra, modified by loicsauteur
"""

import numpy as np
import numpy.testing as nt
import pytest
from qtpy.QtWidgets import QSlider

from napari_filter_labels_by_prop.DoubleSlider import DoubleSlider


def test_if_double_slider_is_subclass_of_QSlider(qtbot):
    slider = DoubleSlider()
    assert isinstance(slider, QSlider)


def test_set_float_value(qtbot):
    slider = DoubleSlider()
    slider.setValue(0.0)
    nt.assert_almost_equal(
        slider.value(),
        0.0,
    )

    slider.setValue(0.6)
    nt.assert_almost_equal(slider.value(), 0.6)


def test_default_min_max_values(qtbot):
    slider = DoubleSlider()
    np.testing.assert_almost_equal(slider.minimum(), 0.0, decimal=2)
    np.testing.assert_almost_equal(slider.maximum(), 1.0, decimal=2)


def test_setting_minimum_value_above_maximum_value(qtbot):
    slider = DoubleSlider()
    with pytest.raises(ValueError):
        slider.setMinimum(2.0)


def test_setting_maximum_value_below_minimum_value(qtbot):
    slider = DoubleSlider()
    with pytest.raises(ValueError):
        slider.setMaximum(-0.5)


def test_valid_limits(qtbot):
    slider = DoubleSlider()
    slider.setMinimum(0.6)
    slider.setMaximum(2.3)
    nt.assert_almost_equal(slider.minimum(), 0.6, decimal=3)
    nt.assert_almost_equal(slider.maximum(), 2.3, decimal=3)

    slider.setMinimum(-5.0)
    slider.setMaximum(-2.0)
    nt.assert_almost_equal(slider.minimum(), -5.0, decimal=3)
    nt.assert_almost_equal(slider.maximum(), -2.0, decimal=3)


def test_setting_value_below_lower_limit(qtbot):
    slider = DoubleSlider()
    slider.setMinimum(0.6)
    slider.setValue(0.2)
    nt.assert_almost_equal(slider.value(), 0.6, decimal=3)


def test_setting_value_above_upper_limit(qtbot):
    slider = DoubleSlider()
    slider.setMaximum(0.6)
    slider.setValue(0.9)
    nt.assert_almost_equal(slider.value(), 0.6, decimal=3)


def test_usual_numbers(qtbot):
    slider = DoubleSlider()
    slider.setMinimum(0.8)
    slider.setMaximum(2.3)
    slider.setValue(1.46)
    nt.assert_almost_equal(slider.value(), 1.46, decimal=2)


def test_negative_range(qtbot):
    slider = DoubleSlider()
    slider.setMinimum(-5.0)
    slider.setMaximum(-1.0)
    slider.setValue(-4.4)
    nt.assert_almost_equal(slider.value(), -4.4, decimal=2)
