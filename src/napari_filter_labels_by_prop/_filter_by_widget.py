import napari.layers
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from skimage.measure import regionprops_table

import napari_filter_labels_by_prop.utils as uts
from napari_filter_labels_by_prop.PropFilter import PropFilter

# TODO add 'experimental' projected region props (tickbox, only available for >3D)


class FilterByWidget(QWidget):
    """
    The base of this widget.

    Sets up
    - the label and image layer selections,
    - populates the measurement drop-box, and
    - initialises the actual PropFilter widget (separate class containing histogram
      with sliders and create button).

    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        # Class variables
        self.lbl_layer_name = None
        self.img_layer_name = None
        self.lbl_combobox = QComboBox()
        self.img_combobox = QComboBox()
        self.shape_match = QLabel("")
        self.projected_props_ckb = QCheckBox("")
        self.shape_match.setStyleSheet("color: red")
        self.props_binary = [
            "label",
            "area",
            "axis_major_length",
            "axis_minor_length",
            "area_convex",
            "euler_number",
            "extent",
            "feret_diameter_max",
            "eccentricity",
            "perimeter",
            "orientation",
            "solidity",
        ]
        self.props_intensity = [
            # removing axes because of possible value errors
            "label",
            "area",
            "axis_major_length",
            "axis_minor_length",
            "area_convex",
            "euler_number",
            "extent",
            "feret_diameter_max",
            "eccentricity",
            "intensity_max",
            "intensity_mean",
            "intensity_min",
            "perimeter",
            "orientation",
            "solidity",
        ]
        # Add intensity_std if skimage is bigger than 0.23.1
        if uts.check_skimage_version():
            self.props_intensity.append("intensity_std")
        self.prop_table = None
        self.lbl = None  # reference to label layer data
        self.img = None
        self.prop_combobox = QComboBox()

        # Create layout
        self.main_layout = QVBoxLayout()
        self.setup_combo_boxes()
        self.setLayout(self.main_layout)
        # Create the actual filter widget
        self.filter_widget = PropFilter(viewer=self.viewer)

        # Initialise combo boxes
        self.init_combo_boxes()
        self.main_layout.addWidget(self.filter_widget)

        # link combo-boxes to changes
        self.viewer.layers.events.inserted.connect(self.on_add_layer)
        self.viewer.layers.events.removed.connect(self.on_remove_layer)
        self.lbl_combobox.currentIndexChanged.connect(
            self.on_lbl_layer_selection
        )
        self.img_combobox.currentIndexChanged.connect(
            self.on_img_layer_selection
        )
        self.prop_combobox.currentIndexChanged.connect(self.on_prop_selection)
        # Connect the projected props checkbox
        self.projected_props_ckb.stateChanged.connect(self.update_properties)

    def on_prop_selection(self, index: int):
        """
        Callback function that updates the selected measurements.
        :param index:
        :return:
        """
        if self.lbl_layer_name is None:
            return
        if index != -1:
            prop = self.prop_combobox.itemText(index)
            # Update the prop_filter --> only the property name to filter on
            self.filter_widget.update_property(prop)

    def update_properties(self):
        if self.lbl is None:
            return
        # Ensure that the img and labels have the same shape for measurements
        intensity_image = None  # to use to measure
        if self.img is None:
            intensity_image = None
            props = self.props_binary.copy()
        elif (
            self.lbl.shape != self.img.shape
            and self.lbl.shape != self.img.shape[:-1]
        ):
            intensity_image = None
            props = self.props_binary.copy()
            # update info label about shape matching
            self.shape_match.setText("Label & Image shapes do not match.")
            self.shape_match.setToolTip(
                f"Label shape = {self.lbl.shape}; "
                f"Image shape = {self.img.shape}"
            )
        else:
            intensity_image = self.img
            props = self.props_intensity.copy()
            # update the info label about shape matching
            self.shape_match.setText("")
            self.shape_match.setToolTip("")

        # Define extra properties
        extra_props = None

        # remove some properties for 3D images (no matter if Z or T)
        if self.lbl.ndim > 2:
            props_to_remove = [
                "axis_major_length",
                "axis_minor_length",
                "area_convex",
                "feret_diameter_max",
                "eccentricity",
                "perimeter",
                "orientation",
                "solidity",
            ]
            for p in props_to_remove:
                props.remove(p)
            # If >3D label image and projected_props checked
            if self.projected_props_ckb.isChecked():
                extra_props = (
                    uts.projected_area,
                    uts.projected_convex_area,
                    uts.projected_circularity,
                    uts.projected_perimeter,
                )

        self.prop_table = regionprops_table(
            self.lbl,
            intensity_image=intensity_image,
            properties=props,
            extra_properties=extra_props,
        )
        # Update the prop_filter widget
        self.filter_widget.update_widget(
            self.lbl_layer_name,
            self.viewer.layers[self.lbl_layer_name],
            self.prop_table,
            "label",  # at initialisation this is always selected
        )
        self.prop_combobox.clear()
        self.prop_combobox.addItems(self.prop_table.keys())
        # Add the properties to the labels layer features data
        self.add_layer_properties()

    def add_layer_properties(self):
        """
        Create a set of measurements added to the label layer properties.

        This will show the measurements at the bottom of the viewer.
        The way this function creates the property dictionary, allows for
        having label images where not every label is present in the image.

        Note: as far as I have seen, the labels layer properties and
        features fields are the same...
        :return:
        """
        # The properties are a dictionary with str measurement,
        # and with value = array of length n (max) labels + 0-label
        features = {}
        label_max = self.prop_table["label"].max()
        for k, v in self.prop_table.items():
            # skipp the 'label' feature
            if k == "label":
                continue
            # Per measurement create a dict entry, including label "0"
            features[k] = ["none"] * (label_max + 1)
            # Assign the proper value to the features values array
            for i, label in enumerate(self.prop_table["label"]):
                features[k][label] = v[i]
        # Add the features to the properties
        self.viewer.layers[self.lbl_layer_name].properties = features

    def on_lbl_layer_selection(self, index: int):
        """
        Callback function that "updates stuff"

        :param index:
        :return:
        """
        # reset the lbl_combobox style sheet
        self.lbl_combobox.setStyleSheet(self.img_combobox.styleSheet())
        self.lbl_combobox.setToolTip("")
        if index != -1:
            self.lbl_layer_name = self.lbl_combobox.itemText(index)
            self.lbl = self.viewer.layers[self.lbl_layer_name].data
            # check if there is any labels there...
            if self.lbl.max() < 1:
                self.lbl = None
                self.filter_widget.hide_widget(clear=True)
                self.lbl_combobox.setStyleSheet("color: red")
                self.lbl_combobox.setToolTip("Label Layer has no labels.")
                return
            self.update_properties()
        else:
            # No labels selected, reset the widget...
            self.lbl_layer_name = None
            self.lbl = None
            self.prop_combobox.clear()
            self.prop_table = None
            self.filter_widget.hide_widget(clear=True)

    def on_img_layer_selection(self, index: int):
        """
        Callback function that "updates stuff"

        :param index:
        :return:
        """
        if index != -1:
            layer_name = self.img_combobox.itemText(index)
            self.img_layer_name = layer_name
            self.img = self.viewer.layers[layer_name].data
            self.update_properties()
        else:
            self.img_layer_name = None
            self.img = None
            self.shape_match.setText("")
            self.shape_match.setToolTip("")

    def on_remove_layer(self, event):
        """
        Callback function that updates the combo boxes when a layer is removed.
        :param event:
        :return:
        """
        layer_name = event.value.name
        if isinstance(event.value, napari.layers.Labels):
            index = self.lbl_combobox.findText(
                layer_name, Qt.MatchExactly
            )  # returns -1 if not found
            if index != -1:
                self.lbl_combobox.removeItem(index)
                # get the new layer selection
                index = self.lbl_combobox.currentIndex()
                layer_name = self.lbl_combobox.itemText(index)
                if layer_name != self.lbl_layer_name:
                    self.lbl_layer_name = layer_name

        elif isinstance(event.value, napari.layers.Image):
            index = self.img_combobox.findText(
                layer_name, Qt.MatchExactly
            )  # returns -1 if not found
            if index != -1:
                self.img_combobox.removeItem(index)
                # get the new layer selection
                index = self.img_combobox.currentIndex()
                layer_name = self.img_combobox.itemText(index)
                if layer_name != self.img_layer_name:
                    self.img_layer_name = layer_name
        else:
            pass

    def on_add_layer(self, event):
        """
        Callback function that updates the combo boxes when a layer is added.

        :param event:
        :return:
        """
        layer_name = event.value.name
        layer = self.viewer.layers[layer_name]
        if isinstance(layer, napari.layers.Labels):
            self.lbl_combobox.addItem(layer_name)
            if self.lbl_layer_name is None:
                self.lbl_layer_name = layer_name
                self.lbl_combobox.setCurrentIndex(0)
        elif isinstance(layer, napari.layers.Image):
            self.img_combobox.addItem(layer_name)
            if self.img_layer_name is None:
                self.img_layer_name = layer_name
                self.img_combobox.setCurrentIndex(0)
        else:
            pass

    def init_combo_boxes(self):
        # label layer entries
        lbl_names = [
            layer.name
            for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Labels)
        ]
        if self.lbl_layer_name is None and len(lbl_names) > 0:
            self.lbl_combobox.addItems(lbl_names)
            self.lbl_layer_name = lbl_names[0]
            index = self.lbl_combobox.findText(
                self.lbl_layer_name, Qt.MatchExactly
            )
            self.lbl_combobox.setCurrentIndex(index)
        # image layer entries
        img_names = [
            layer.name
            for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Image)
        ]
        if self.img_layer_name is None and len(img_names) > 0:
            self.img_combobox.addItems(img_names)
            self.img_layer_name = img_names[0]
            index = self.img_combobox.findText(
                self.img_layer_name, Qt.MatchExactly
            )
            self.img_combobox.setCurrentIndex(index)
        # Set the image layer data class variable
        if self.img_layer_name is not None:
            self.img = self.viewer.layers[self.img_combobox.itemText(0)].data
        # Set the label layer data class variable and load measurements
        if self.lbl_layer_name is not None:
            self.lbl = self.viewer.layers[self.lbl_combobox.itemText(0)].data
            self.update_properties()

    def setup_combo_boxes(self):
        # Label selection entry
        lbl_widget = QWidget()
        lbl_layout = QHBoxLayout()
        lbl_title = QLabel("Label")
        lbl_title.setToolTip("Choose a label layer.")
        lbl_layout.addWidget(lbl_title)
        lbl_layout.addWidget(self.lbl_combobox)
        # Image selection entry
        img_widget = QWidget()
        img_layout = QHBoxLayout()
        img_title = QLabel("Image")
        img_title.setToolTip("Choose an image layer.")
        img_layout.addWidget(img_title)
        img_layout.addWidget(self.img_combobox)
        # Checkbox for 3D projected properties
        project_widget = QWidget()
        project_layout = QHBoxLayout()
        project_title = QLabel("Measure projected shape properties")
        project_tip = "Measure shape properties for projected 3D labels?"
        project_title.setToolTip(project_tip)
        self.projected_props_ckb.setToolTip(
            "Measures projected circularity, perimeter and convex hull area"
        )
        self.projected_props_ckb.setChecked(True)
        project_layout.addWidget(project_title)
        project_layout.addWidget(self.projected_props_ckb)
        # Measurement/property selection entry
        prop_widget = QWidget()
        prop_layout = QHBoxLayout()
        prop_title = QLabel("Measurement")
        prop_title.setToolTip("Select the measurement to filter on.")
        prop_layout.addWidget(prop_title)
        prop_layout.addWidget(self.prop_combobox)
        # add widgets to the main widget
        lbl_widget.setLayout(lbl_layout)
        img_widget.setLayout(img_layout)
        prop_widget.setLayout(prop_layout)
        project_widget.setLayout(project_layout)
        self.main_layout.addWidget(lbl_widget)
        self.main_layout.addWidget(img_widget)
        self.main_layout.addWidget(self.shape_match)
        self.main_layout.addWidget(project_widget)
        self.main_layout.addWidget(prop_widget)
