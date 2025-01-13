import napari.layers
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from napari_filter_labels_by_prop.DoubleSlider import DoubleSlider


class PropFilter(QWidget):
    """
    That's were the filtering on the properties is done.

    Shows (a histogram of selected property) and slides to filter on the properties
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        # Class variables
        self.viewer = viewer
        self.lbl_name = None
        self.props_table = None
        self.layer = None
        self.prop = None
        self.original_colormap = None
        self.colormap = None

        self.min = QLabel("")
        self.max = QLabel("")
        self.min_label = QLabel("Min")
        self.max_label = QLabel("Max")

        # Create layout
        self.layout = QVBoxLayout()
        self.histo = QPushButton(
            "place holder button"
        )  # FIXme place holder for histogram image
        self.min_slider = DoubleSlider()  # FIXME -> put back to None
        self.max_slider = DoubleSlider()  # FIXME -> put back to None
        self.create_btn = QPushButton("Create Labels")
        self.create_btn.clicked.connect(self.create_labels)

        self.layout.addWidget(self.histo, Qt.AlignHCenter)
        self.setup_sliders()
        self.layout.addWidget(self.create_btn, Qt.AlignHCenter)
        self.setLayout(self.layout)

    def update_property(self, prop: str):
        print('in "update_property" =', prop)
        self.prop = prop
        # Make sure to show the widget
        self.show_widget()

        # TODO: create histogram

        # TODO: update sliders
        self.update_sliders()

    def update_sliders(self):
        if self.prop is None:
            print("! update sliders > property was NONE")
            return
        prop_values = self.props_table[self.prop]
        # For sliders the values should be of type int
        _min = int(prop_values.min())
        _max = int(prop_values.max())
        print("property minimum value=", _min)
        print("property maximum value=", _max)
        if _min < 0:
            self.min_slider.setMinimum(_min)
            self.max_slider.setMinimum(_min)
        self.min_slider.setMaximum(_max)
        self.max_slider.setMaximum(_max)
        self.min_slider.setValue(_min)
        self.max_slider.setValue(_max)

        # TODO if min values are minus, i have to adjust both slides accordingly...

    def update_widget(
        self,
        lbl_name: str,
        layer: napari.layers.Labels,
        props_table: dict,
        prop=str,
    ):
        # Set class variables
        self.lbl_name = lbl_name
        self.layer = layer
        self.props_table = props_table
        self.prop = prop
        # show the widget
        self.show_widget()
        # FIXME TEMP
        print("property table min/max values")
        for k, v in props_table.items():
            print(k, ":", v.min(), "-", v.max())
        print()

        # TODO: create histogram

        # TODO: update sliders
        self.update_sliders()

        # TODO: create custom 'original' LUT / colormap

    def hide_widget(self):
        # TODO hide histogram
        self.min_slider.setVisible(False)
        self.max_slider.setVisible(False)
        self.min.setHidden(True)
        self.max.setHidden(True)
        self.min_label.setHidden(True)
        self.max_label.setHidden(True)
        self.create_btn.setDisabled(True)
        # TODO ?? Reset colormap ??

    def show_widget(self):
        # TODO show histogram
        self.min_slider.setVisible(True)
        self.max_slider.setVisible(True)
        self.min.setHidden(False)
        self.max.setHidden(False)
        self.min_label.setHidden(False)
        self.max_label.setHidden(False)
        self.create_btn.setDisabled(False)

    '''
    def get_min(self):
        """
        Get the minimum slider value.

        :return:
        """
        # FIXME currently unused
        pass'''

    def update_min(self):
        """
        Updates on changes on the min_slider.

        :return:
        """
        self.min.setText(str(self.min_slider.value()))
        # Fixme update colormap

    def update_max(self):
        """
        Updates on changes on the max_slider.
        :return:
        """
        self.max.setText(str(self.max_slider.value()))
        # Fixme update colormap

    def create_labels(self):
        """
        Final function to create new labels layer.

        :return:
        """
        print("button was clicked")
        self.histo = QLabel("Placeholder")

    def setup_sliders(self):
        # Create default slides
        self.min_slider = DoubleSlider(Qt.Orientation.Horizontal)
        self.max_slider = DoubleSlider(Qt.Orientation.Horizontal)
        self.max_slider.setValue(self.max_slider.maximum())
        self.min_slider.valueChanged.connect(self.update_min)
        self.max_slider.valueChanged.connect(self.update_max)

        # Create Gridlayout for sliders onlay
        grid_widget = QWidget()
        grid = QGridLayout()
        grid.setSpacing(2)
        grid.addWidget(self.min_label, 0, 0, Qt.AlignLeft)
        grid.addWidget(self.min_slider, 0, 1)
        grid.addWidget(self.min, 1, 1, Qt.AlignHCenter)
        grid.addWidget(self.max_label, 2, 0, Qt.AlignLeft)
        grid.addWidget(self.max_slider, 2, 1)
        grid.addWidget(self.max, 3, 1, Qt.AlignHCenter)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 10)
        print("grid min size hint:", grid_widget.minimumSizeHint().height())
        grid_widget.setLayout(grid)
        self.layout.addWidget(grid_widget)
        print("grid min size hint:", grid_widget.minimumSizeHint().height())

        # Make the grid tighter...
        grid_widget.setMaximumHeight(
            grid_widget.minimumSizeHint().height() + 10
        )
        label_width = 25
        if (
            self.min_label.minimumSizeHint().width()
            > self.max_label.minimumSizeHint().width()
        ):
            label_width = self.min_label.minimumSizeHint().width() + 3
            print("width set to minlable")
        else:
            label_width = self.max_label.minimumSizeHint().width() + 3
            print("width set to maxlable")
        self.min_label.setMaximumWidth(label_width)
        self.max_label.setMaximumWidth(label_width)

        # At setup, still hide the entries
        self.hide_widget()
