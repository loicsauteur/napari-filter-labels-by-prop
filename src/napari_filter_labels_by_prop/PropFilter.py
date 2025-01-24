import napari.layers
import numpy as np
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as Canvas,
)
from matplotlib.figure import Figure
from napari.utils.colormaps import DirectLabelColormap, label_colormap
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import napari_filter_labels_by_prop.utils as uts
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
        self.color_dict = None
        self.labels_to_hide = []

        # Sliders
        self.min_slider = DoubleSlider()
        self.max_slider = DoubleSlider()
        self.min = QLabel("")
        self.max = QLabel("")
        self.min_label = QLabel("Min")
        self.max_label = QLabel("Max")

        # Histogram plot
        self.histo_canvas = Canvas(Figure(figsize=(3, 3)))  # cannot hide it??
        self.ax = self.histo_canvas.figure.subplots()
        self.ax.axis("off")  # makes plot all white (hiding axes)
        self.barplot = None

        # Create new label layer button
        self.create_btn = QPushButton("Create Labels")
        self.create_btn.clicked.connect(self.create_labels)

        # Create layout
        self.layout = QVBoxLayout()
        # 1) add canvas for histogram
        self.layout.addWidget(self.histo_canvas, Qt.AlignHCenter)
        # 2) add sliders for adjusting min and max values
        self.setup_sliders()
        # 3) add create new laybel layer button
        self.layout.addWidget(self.create_btn, Qt.AlignHCenter)
        self.setLayout(self.layout)

    def update_histo(self):
        """
        Updates the histogram plot in the widget.

        :return:
        """
        values = self.props_table[self.prop]
        # show log y-axis if min/max values difference > 100
        counts, bins = np.histogram(values)
        do_log = counts.max() - counts.min() > 100
        self.ax.axis("on")
        if self.barplot is None:
            self.barplot = self.ax.hist(
                x=values,
                bins=len(self.props_table["label"]),
                histtype="stepfilled",
                log=do_log,
            )
        else:
            self.ax.clear()
            self.barplot = self.ax.hist(
                x=values,
                bins=len(self.props_table["label"]),
                histtype="stepfilled",
                log=do_log,
            )

        # removes ticks from y-axis
        self.ax.set_yticks([])
        # update the canvas
        self.histo_canvas.draw()

    def update_property(self, prop: str):
        """
        Called when property is selected.

        Will update the histogram and the sliders.
        :param prop: str property of interest
        :return:
        """
        if self.layer is None:
            # in case this widget has not been yet setup
            return
        self.prop = prop
        # print(self.prop, 'min/max=',
        #      self.props_table[self.prop].min(),
        #      self.props_table[self.prop].max())
        # Make sure to show the widget
        self.show_widget()

        # Create histogram
        self.update_histo()

        # Update sliders
        self.update_sliders()

    def update_sliders(self):
        """
        Adjust min and max of the sliders.

        :return:
        """
        if self.prop is None:
            return
        prop_values = self.props_table[self.prop]

        # For sliders the values should be of type int - not anymore since Double slider
        _min = prop_values.min()
        _max = prop_values.max()
        self.min_slider.setRange(_min, _max)
        self.max_slider.setRange(_min, _max)
        self.min_slider.setValue(_min)
        self.max_slider.setValue(_max)
        # Make sure to update also the min/max value display
        self.update_min()
        self.update_max()
        # Reset layer colormap
        self.update_color_map()

    def update_widget(
        self,
        lbl_name: str,
        layer: napari.layers.Labels,
        props_table: dict,
        prop=str,
    ):
        """
        Set up the data of this widget.

        :param lbl_name: str label layer name
        :param layer: napari label layer
        :param props_table: (dict) regionprops_table of the labels
        :param prop: str selected property
        :return:
        """
        # Set class variables
        self.lbl_name = lbl_name
        self.layer = layer
        self.props_table = props_table
        self.prop = prop

        # remember the origianl colormap
        self.original_colormap = self.layer.colormap
        # Create custom 'original' LUT / colormap
        n_labels = self.layer.data.max() + 1
        colormap = label_colormap(num_colors=n_labels)
        color_dict = dict(enumerate(colormap.colors[1:n_labels], start=1))
        color_dict[None] = "transparent"
        color_dict[0] = "transparent"
        colormap = DirectLabelColormap(color_dict=color_dict)
        self.color_dict = colormap.color_dict
        # Apply the custom colormap to the labels layer
        self.layer.colormap = colormap

        # show the widget
        self.show_widget()

        # Update sliders
        self.update_sliders()

    def hide_widget(self, clear: bool = False):
        """
        Hides the widget and it's content.

        :param clear: boolean to clear the plot data, since
                    plot cannot easily be hidden.
        :return:
        """
        if clear:
            # and clear the canvas (remove plot bars)
            self.ax.clear()
        # 'hide' histogram - makes it all white
        self.ax.axis("off")
        self.min_slider.setVisible(False)
        self.max_slider.setVisible(False)
        self.min.setHidden(True)
        self.max.setHidden(True)
        self.min_label.setHidden(True)
        self.max_label.setHidden(True)
        self.create_btn.setDisabled(True)
        # Reset colormap
        if self.layer is not None:
            self.layer.colormap = self.original_colormap

    def show_widget(self):
        """
        Helper function to show the elements of the widget.

        :return:
        """
        self.min_slider.setVisible(True)
        self.max_slider.setVisible(True)
        self.min.setHidden(False)
        self.max.setHidden(False)
        self.min_label.setHidden(False)
        self.max_label.setHidden(False)
        self.create_btn.setDisabled(False)
        self.update_histo()

    def on_min_slider_release(self):
        """
        On min slider release, trigger viewer update.

        :return:
        """
        self.update_color_map()

    def on_max_slider_release(self):
        """
        On max slider release, trigger viewer update.

        :return:
        """
        self.update_color_map()

    def update_color_map(self):
        """
        Modify the color_dict and create new colormap for labels layer.

        Sets the alpha of labels to hide or show to 0 or 1, respectively.
        New colormap is generated each time.
        :return:
        """
        self.labels_to_hide.clear()
        _min = self.min_slider.value()
        _max = self.max_slider.value()
        self.label_values = self.props_table[self.prop]
        for i in range(len(self.label_values)):
            if self.label_values[i] < _min:
                self.labels_to_hide.append(self.props_table["label"][i])
            if self.label_values[i] > _max:
                self.labels_to_hide.append(self.props_table["label"][i])
        # Add 'None' and '0' keys to labels_to_hide
        self.labels_to_hide.append(None)
        self.labels_to_hide.append(0)
        # Update the color map via modification of the color dict
        for k, v in self.color_dict.items():
            # Put alpha to 0 for label to hide
            if k in self.labels_to_hide:
                v[3] = 0.0
            # Ensure alpha is 1 for labels to be shown
            else:
                v[3] = 1.0
        # Create and apply the colormap
        colormap = DirectLabelColormap(color_dict=self.color_dict)
        self.layer.colormap = colormap

    def update_min(self):
        """
        Updates on changes on the min_slider on value change.

        Will update only the self.min field
        Will update the color map if there is less than 100 labels.
        :return:
        """
        # Make sure that the value is not bigger than the max slider value
        if self.min_slider.value() > self.max_slider.value():
            self.min_slider.setValue(self.max_slider.value())
        _min = self.min_slider.value()
        if isinstance(_min, float):
            self.min.setText(str(round(self.min_slider.value(), 4)))
        else:
            self.min.setText(str(self.min_slider.value()))
        if len(self.props_table[self.prop]) < 100:
            self.update_color_map()

    def update_max(self):
        """
        Updates on changes on the max_slider on value change.

        Will update only the self.max field.
        Will update the color map if there is less than 100 labels.
        :return:
        """
        # Make sure taht the value is not smaller than the min slider value
        if self.max_slider.value() < self.min_slider.value():
            self.max_slider.setValue(self.min_slider.value())
        _max = self.max_slider.value()
        if isinstance(_max, float):
            self.max.setText(str(round(self.max_slider.value(), 4)))
        else:
            self.max.setText(str(self.max_slider.value(), 4))
        if len(self.props_table[self.prop]) < 100:
            self.update_color_map()

    def create_labels(
        self,
    ):
        """
        Final function to create new labels layer.

        Parameters are here for future use of function not in class
        :param lbl: np.ndarry of label layer to modify.
        :param to_hide: list of int, for labels that should be set to 0
        :return:
        """
        # TODO / FIXME parallelization would be nice
        new_lbl = uts.remove_label_objects(
            self.layer.data, self.labels_to_hide
        )
        self.viewer.add_labels(
            new_lbl,
            name=self.layer.name + "_1",
            multiscale=False,
        )

    def setup_sliders(self):
        """
        Setting up of the slider section of the widget.

        :return:
        """
        # Create default slides
        self.min_slider = DoubleSlider(Qt.Orientation.Horizontal)
        self.max_slider = DoubleSlider(Qt.Orientation.Horizontal)
        self.max_slider.setValue(self.max_slider.maximum())
        self.min_slider.setValue(self.min_slider.minimum())
        self.min_slider.valueChanged.connect(self.update_min)
        self.max_slider.valueChanged.connect(self.update_max)
        self.min_slider.sliderReleased.connect(self.on_min_slider_release)
        self.max_slider.sliderReleased.connect(self.on_max_slider_release)

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
        grid_widget.setLayout(grid)
        self.layout.addWidget(grid_widget)

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
        else:
            label_width = self.max_label.minimumSizeHint().width() + 3
        self.min_label.setMaximumWidth(label_width)
        self.max_label.setMaximumWidth(label_width)

        # At setup, still hide the entries
        self.hide_widget()
