import napari.layers
import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
from skimage.measure import regionprops_table

import napari_filter_labels_by_prop.utils as uts
from napari_filter_labels_by_prop.PropFilter import PropFilter


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
        self.compartments_cbx = QCheckBox("")
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
        # Image calibration
        self.voxel_size = (1.0, 1.0, 1.0)
        self.scale_label = QLabel("Voxel size")
        self.z_textbox = QLineEdit()
        self.y_textbox = QLineEdit()
        self.x_textbox = QLineEdit()
        self.set_btn = QPushButton("Set")

        # Compartment masks
        self.lbl_cells = None
        self.lbl_cyto = None

        # Create layout
        self.main_layout = QGridLayout()
        grid_row = self.setup_layout()
        self.setLayout(self.main_layout)
        # Create the actual filter widget
        self.filter_widget = PropFilter(viewer=self.viewer)

        # Initialise combo boxes
        self.init_combo_boxes()
        self.main_layout.addWidget(self.filter_widget, grid_row, 0, 1, -1)

        # Link combo-boxes to changes
        self.viewer.layers.events.inserted.connect(self.on_add_layer)
        self.viewer.layers.events.removed.connect(self.on_remove_layer)
        self.lbl_combobox.currentIndexChanged.connect(
            self.on_lbl_layer_selection
        )
        self.img_combobox.currentIndexChanged.connect(
            self.on_img_layer_selection
        )
        self.prop_combobox.currentIndexChanged.connect(self.on_prop_selection)
        # Connect the pixel size set button
        self.set_btn.clicked.connect(self.click_set_btn)
        # Connect the projected props checkbox
        self.projected_props_ckb.stateChanged.connect(self.update_properties)
        # Connect the compartment creation checkbox
        self.compartments_cbx.stateChanged.connect(self.create_compartments)

    def create_compartments(self, force: bool = False):
        """
        Create cyto and cell masks.

        Will not create compartments if the checkbox is not checked.
        Will only create compartments if they do not exist already, unless
        the force option is used.

        :param force: in case the mask creation should be forces
                      (e.g. on voxel_size change).
        :return:
        """
        # Don't do anything if there is no label image to begin with
        if self.lbl is None:
            return
        if not self.compartments_cbx.isChecked():
            self.update_properties()
            return
        # Only create the masks if they do not exist already
        if self.lbl_cells is None or force:
            # scale changes? --> only considered when set button
            self.lbl_cells, self.lbl_cyto = uts.create_cell_cyto_masks(
                lbl=self.lbl, expansion=5, voxel_size=self.voxel_size
            )
            self.update_properties()

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

    def click_set_btn(self):
        # set the scale in the layers
        # 2D
        if len(self.viewer.layers[self.lbl_layer_name].scale) == 2:
            self.voxel_size = (
                float(self.y_textbox.text()),
                float(self.x_textbox.text()),
            )
            self.viewer.layers[self.lbl_layer_name].scale = self.voxel_size
            if self.img_layer_name is not None:
                self.viewer.layers[self.img_layer_name].scale = self.voxel_size
        # 3D
        elif len(self.viewer.layers[self.lbl_layer_name].scale) == 3:
            self.voxel_size = (
                float(self.z_textbox.text()),
                float(self.y_textbox.text()),
                float(self.x_textbox.text()),
            )
            self.viewer.layers[self.lbl_layer_name].scale = self.voxel_size
            if self.img_layer_name is not None:
                self.viewer.layers[self.img_layer_name].scale = self.voxel_size
        else:
            raise NotImplementedError(
                f"Setting the scale for more than "
                f"{len(self.viewer.layers[self.lbl_layer_name].scale)}D images "
                f"is not supported"
            )
        # (Re-)create the masks for compartments (only happens if checkbox ticked)
        self.create_compartments(force=True)
        # Update the properties
        self.update_properties()

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
            self.img = None
            self.img_layer_name = None
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
            spacing=self.voxel_size,
        )
        self.calibrate_extra_props()
        # Measure intensity props in compartments
        self.measure_compartment_props(
            intensity_image=intensity_image, props=props
        )

        # Update the prop_filter widget
        self.filter_widget.update_widget(
            lbl_name=self.lbl_layer_name,
            layer=self.viewer.layers[self.lbl_layer_name],
            props_table=self.prop_table,
            prop="label",  # at initialisation this is always selected
        )
        # Set the compartment masks in the FilterProp
        self.filter_widget.set_compartment_masks(
            cells=self.lbl_cells, cyto=self.lbl_cyto
        )
        self.prop_combobox.clear()
        self.prop_combobox.addItems(self.prop_table.keys())
        # Add the properties to the labels layer features data
        self.add_layer_properties()

    def measure_compartment_props(
        self, intensity_image: np.ndarray, props: list
    ):
        # Don't measure if checkbox is not ticked
        if not self.compartments_cbx.isChecked():
            return
        # Make sure that the masks exist (check one is enough)
        if self.lbl_cyto is None:
            return
        # Create the region prop tables
        table_cyto = regionprops_table(
            self.lbl_cyto,
            intensity_image=intensity_image,
            properties=props,
            spacing=self.voxel_size,
        )
        table_cell = regionprops_table(
            self.lbl_cells,
            intensity_image=intensity_image,
            properties=props,
            spacing=self.voxel_size,
        )
        # Rename the table headers (to include compartments)
        table_cyto = uts.rename_dict_keys(table_cyto, prefix="Cyto")
        table_cell = uts.rename_dict_keys(table_cell, prefix="Cell")
        self.prop_table = uts.rename_dict_keys(
            self.prop_table, prefix="Nucleus"
        )
        # Merge the 3 tables into self.prop_table
        self.prop_table = uts.merge_dict(self.prop_table, table_cell)
        self.prop_table = uts.merge_dict(self.prop_table, table_cyto)

    def calibrate_extra_props(self):
        # check that the keys are in the props table
        from napari_filter_labels_by_prop.utils import (
            __calibrated_extra_props__,
        )

        for p in __calibrated_extra_props__:
            if p not in self.prop_table:
                return
        # if x != y size, raise not implemented error
        if self.voxel_size[-2] != self.voxel_size[-1]:
            raise NotImplementedError(
                f"Different XY pixel size is not implemented. Got "
                f"({self.voxel_size[-2]}, {self.voxel_size[-1]})."
            )
        # multiply the values
        for prop in __calibrated_extra_props__:
            if "area" in prop:
                self.prop_table[prop] = (
                    self.prop_table[prop] * self.voxel_size[-1] ** 2
                )
            else:
                self.prop_table[prop] = (
                    self.prop_table[prop] * self.voxel_size[-1]
                )

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

    def check_and_set_scale(
        self,
        scale: tuple,
        overwrite: bool = False,
        is_img_layer: bool = False,
    ):
        """
        Check the scale read from the image(s).

        If scale is OK, will set the corresponding text-boxes and
        the voxel-size variable.
        But it does not set the layer scale, this only happens when the
        set button is pressed.

        :param scale: tuple of image layer scale
        :param overwrite: bool whether to overwrite the scale.
                          If False, it will still overwrite if the image-scale is not
                          all 1.'s Default is False.
        :param is_img_layer: whether the trigger comes from the image layer or not.
                             Default is False.
        :return:
        """

        # On label layer change and image_layer(_name) is available
        if not is_img_layer and self.img is not None:
            # Favor image layer scale
            img_scale = self.viewer.layers[self.img_layer_name].scale
            # If label and image layer scales are not the same?
            if not np.array_equal(img_scale, scale):
                # Check whether all values are 1,
                for s in img_scale:
                    # If not use the image scale for pixel size
                    if s != 1.0:
                        scale = img_scale
                        break

        # Force to read the voxel size, i.e. when new label layer is selected
        if self.x_textbox.text() == str(np.nan):
            overwrite = True

        # 2D
        if len(scale) == 2:
            # skip if not overwrite and the image scale is all 1. (uncalibrated)
            if not overwrite and np.array_equal(scale, np.array([1.0, 1.0])):
                return
            # disable the z textbox
            self.z_textbox.setDisabled(True)
            # set the description
            self.scale_label.setText("Pixel size")
            y = float(self.x_textbox.text())
            x = float(self.y_textbox.text())
            if not np.array_equal(scale, np.array([y, x])):
                # update the scale text boxes
                self.y_textbox.setText(str(scale[0]))
                self.x_textbox.setText(str(scale[1]))
                # set the voxel size
                self.voxel_size = (scale[0], scale[1])
            # Disable the extra_properties checkbox
            self.projected_props_ckb.setChecked(
                False
            )  # FYI this triggers prop update
            self.projected_props_ckb.setDisabled(True)
        # 3D
        else:
            # skip if not overwrite and the image scale is all 1. (uncalibrated)
            if not overwrite and np.array_equal(
                scale, np.array([1.0, 1.0, 1.0])
            ):
                return
            # enable the z textbox
            self.z_textbox.setDisabled(False)
            # set the description
            self.scale_label.setText("Voxel size")
            z = float(self.z_textbox.text())
            y = float(self.x_textbox.text())
            x = float(self.y_textbox.text())
            if not np.array_equal(scale, np.array([z, y, x])):
                # update the scale text boxes
                self.z_textbox.setText(str(scale[0]))
                self.y_textbox.setText(str(scale[1]))
                self.x_textbox.setText(str(scale[2]))
                # set the voxel size
                self.voxel_size = (scale[0], scale[1], scale[2])
            # Enable the extra_properties checkbox
            self.projected_props_ckb.setDisabled(False)

    def reset_voxel_size(self):
        """
        Reset the voxel size and the text boxes.

        Used upon label layer change.
        :return:
        """
        self.voxel_size = (1.0, 1.0, 1.0)
        self.z_textbox.setText(str(np.nan))
        self.y_textbox.setText(str(np.nan))
        self.x_textbox.setText(str(np.nan))

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
            # Reset the voxel size
            self.reset_voxel_size()
            # Reset the  cell & cyto masks
            self.lbl_cells = None
            self.lbl_cyto = None
            # Load the layer to class variables
            self.lbl_layer_name = self.lbl_combobox.itemText(index)
            self.lbl = self.viewer.layers[self.lbl_layer_name].data
            # check if there is any labels there...
            if self.lbl.max() < 1:
                self.lbl = None
                self.filter_widget.hide_widget(clear=True)
                self.lbl_combobox.setStyleSheet("color: red")
                self.lbl_combobox.setToolTip("Label Layer has no labels.")
                return
            scale = self.viewer.layers[self.lbl_layer_name].scale
            self.check_and_set_scale(scale=scale)
            # Check whether the compartment check box is check to create masks
            if self.compartments_cbx.isChecked():
                self.create_compartments()
            self.update_properties()
        else:
            # No labels selected, reset the widget...
            self.lbl_layer_name = None
            self.lbl = None
            self.lbl_cyto = None
            self.lbl_cells = None
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
            scale = self.viewer.layers[layer_name].scale
            self.check_and_set_scale(scale=scale, is_img_layer=True)
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
            scale = self.viewer.layers[self.lbl_combobox.itemText(0)].scale
            self.check_and_set_scale(scale=scale)
            self.update_properties()

    def setup_layout(self) -> int:
        """
        Set up the widget layout.

        Adds label choice, image choice, info about shape miss-match,
        image calibration setter, compartment measure choice,
        projected shape choice, measurement choice.

        Does not add the PropFilter widget, this is added after initialisation.
        :return: int of next row to add elements to grid-layout
        """
        row = 0
        # Label selection entry
        lbl_title = QLabel("Label")
        lbl_title.setToolTip("Choose a label layer.")
        self.main_layout.addWidget(
            lbl_title, row, 0, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.main_layout.addWidget(self.lbl_combobox, row, 1, 1, -1)
        row += 1
        # Image selection entry
        img_title = QLabel("Image")
        img_title.setToolTip("Choose an image layer.")
        self.main_layout.addWidget(
            img_title, row, 0, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.main_layout.addWidget(self.img_combobox, row, 1, 1, -1)
        row += 1
        self.main_layout.addWidget(self.shape_match, row, 0, 1, -1)
        row += 1
        # Image calibration entry
        self.z_textbox.setToolTip("Z voxel size")
        self.z_textbox.setValidator(QDoubleValidator(0.001, 1000.0, 3))
        self.z_textbox.setText(str(np.nan))
        self.z_textbox.setMaximumWidth(50)
        self.y_textbox.setToolTip("Y pixel size")
        self.y_textbox.setValidator(QDoubleValidator(0.001, 1000.0, 3))
        self.y_textbox.setText(str(np.nan))
        self.y_textbox.setMaximumWidth(50)
        self.x_textbox.setToolTip("X pixel size")
        self.x_textbox.setValidator(QDoubleValidator(0.001, 1000.0, 3))
        self.x_textbox.setText(str(np.nan))
        self.x_textbox.setMaximumWidth(50)
        self.scale_label.setToolTip(
            "Allows shape measurements in calibrated units."
        )
        self.set_btn.setToolTip(
            "Set the pixel calibration to the selected layer(s)."
        )
        self.main_layout.addWidget(
            self.scale_label, row, 0, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.main_layout.addWidget(self.z_textbox, row, 1)
        self.main_layout.addWidget(self.y_textbox, row, 2)
        self.main_layout.addWidget(self.x_textbox, row, 3)
        self.main_layout.addWidget(self.set_btn, row, 4)
        row += 1
        # Checkbox for compartment measurements
        comp_title = QLabel("Measure cytoplasm and cell compartments")
        comp_title.setToolTip(
            "Assuming your labels are nuclei, measure properties in "
            "additional compartments, created by expansion of 5 "
            "units."
        )
        self.main_layout.addWidget(
            comp_title, row, 0, 1, 4, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.compartments_cbx.setChecked(False)
        self.main_layout.addWidget(
            self.compartments_cbx, row, 4, Qt.AlignmentFlag.AlignRight
        )
        row += 1
        # Checkbox for 3D projected properties
        project_title = QLabel("Measure projected shape properties")
        project_title.setToolTip(
            "Measure shape properties for projected 3D labels?"
        )
        self.projected_props_ckb.setToolTip(
            "Measures projected circularity, perimeter and convex hull area"
        )
        self.projected_props_ckb.setChecked(False)
        self.main_layout.addWidget(
            project_title, row, 0, 1, 4, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.main_layout.addWidget(
            self.projected_props_ckb,
            row,
            4,
            alignment=Qt.AlignmentFlag.AlignRight,
        )
        row += 1
        # Measurement/property selection entry
        prop_title = QLabel("Measurement")
        prop_title.setToolTip("Select the measurement to filter on.")
        self.main_layout.addWidget(
            prop_title, row, 0, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.main_layout.addWidget(self.prop_combobox, row, 1, 1, -1)
        row += 1
        return row
