from qtpy.QtWidgets import QSlider


class DoubleSlider(QSlider):
    """
    This is copied from: https://gist.github.com/dennis-tra/994a65d6165a328d4eabaadbaedac2cc

    Author: dennis-tra
    Modification by loicsauteur: added setRange function (overwrite)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decimals = 5
        self._max_int = 10**self.decimals

        super().setMinimum(0)
        super().setMaximum(self._max_int)

        self._min_value = 0.0
        self._max_value = 1.0

    @property
    def _value_range(self):
        return self._max_value - self._min_value

    def value(self):
        return (
            float(super().value()) / self._max_int * self._value_range
            + self._min_value
        )

    def setValue(self, value):
        super().setValue(
            int((value - self._min_value) / self._value_range * self._max_int)
        )

    def setMinimum(self, value):
        if value > self._max_value:
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._min_value = value
        self.setValue(self.value())

    def setMaximum(self, value):
        if value < self._min_value:
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._max_value = value
        self.setValue(self.value())

    def setRange(self, _min: int, _max: int):
        if _min == _max:
            _min = _min - 0.1
            _max = _max + 0.1
        # avoid having the max at 0 (avoiding 0 divisions)
        if _max == 0:
            _max = _max + 0.1
        if _min > _max:
            raise ValueError(
                "Minimum limit cannot be higher than maximum limit"
            )
        self._min_value = _min
        self._max_value = _max
        self.setMinimum(_min)
        self.setMaximum(_max)

    def minimum(self):
        return self._min_value

    def maximum(self):
        return self._max_value
