from time import time
from typing import Dict, List, Union

import numpy as np
from napari.utils import progress
from skimage.measure import regionprops
from skimage.segmentation import expand_labels, relabel_sequential
from skimage.util import map_array

__calibrated_extra_props__ = [
    "projected_perimeter",
    "projected_convex_area",
    "projected_area",
]


def remove_labels(
    img: np.ndarray, label_map: Dict[int, int], relabel: bool = False
) -> np.ndarray:
    """
    Returns a new label image wih label removed.

    Uses skimage.util.map_array, which is fast.
    map_array requires a list of input_val = ALL label indices, and
    output_vals, which is a list of same length as input_val and maps,
    the values (e.g. same label value for labels to keep, or 0 for the ones to remove).
    :param img: label image
    :param label_map: dict of {label: [label or 0]}
    :param relabel: whether to relabel the new image or keep the original label ids.
                    Default is False.
    :return: new label image with labels removed
    """
    in_vals = np.array(list(label_map.keys()), dtype=int)
    out_vals = np.array(list(label_map.values()), dtype=int)
    new_labels = map_array(
        input_arr=img, input_vals=in_vals, output_vals=out_vals
    )
    if relabel:
        new_labels, _, _ = relabel_sequential(new_labels)
    return new_labels


def remove_label_objects(
    img: np.ndarray, labels: List[int], n_total_labels: int = None
) -> np.ndarray:
    """
    @Deprecated

    Previously used function, which is slow.

    Function to remove label items from image.
    Labels to remove are set to 0 one at a time.

    :param img: label image
    :param labels: List of label to remove. Usually contains None & 0
    :param n_total_labels: total labels in image, currently unused
    :return: new label image
    """
    # Todo find a way to invert labels to remove,
    #  ie. when there is more than total/2
    #   I dont think multiprocessing is possible,
    #   since i need the keep working on modified arrays
    copy = np.ndarray.copy(img)
    # Use process for iteration to show progress in napari activity
    # start = time.time()
    for _label in progress(labels):
        if _label is not None and _label != 0:
            # find indices where equal label
            a = copy == _label
            # set image where indices True to 0
            copy[a] = 0
    # print('time single process =', time.time() - start)
    return copy


def check_skimage_version(
    major: int = 0, minor: int = 23, micro: int = 1
) -> bool:
    """
    Check if the installed skimage version is bigger than major.minor.micro
    Default minimal skimage version = 0.23.1
    :param major:
    :param minor:
    :param micro:
    :return: boolean
    """
    import skimage

    v = skimage.__version__.split(".")
    if int(v[0]) > major:
        return True
    elif int(v[0]) < major:
        return False
    else:
        if int(v[1]) > minor:
            return True
        elif int(v[1]) < minor:
            return False
        else:
            try:
                v3 = int(v[2])
            except ValueError:
                return False
            return v3 > micro


def projected_circularity(region_mask: np.ndarray) -> float:
    """
    Calculate the projected circularity of a region.

    (Using perimeter_crofton as it gives more reasonable circularity values)

    Circularity = 4 * pi * Area / Perimeter^2

    :param region_mask: mask of a region
    :return: Circularity
    """
    img_proj = project_mask(region_mask)
    props = regionprops(img_proj)
    circularity = (4 * np.pi * props[0].area) / (
        props[0].perimeter_crofton ** 2
    )
    return circularity


def projected_perimeter(region_mask: np.ndarray) -> float:
    """
    Calculate the projected perimeter of a region.

    :param region_mask: mask of a region
    :return: Perimeter
    """
    img_proj = project_mask(region_mask)
    props = regionprops(img_proj)
    return props[0].perimeter


def projected_convex_area(region_mask: np.ndarray) -> int:
    """
    Calculate the projected hull area of a region.

    :param region_mask: mask of a region
    :return: convex hull area
    """
    img_proj = project_mask(region_mask)
    props = regionprops(img_proj)
    return props[0].area_convex


def projected_area(region_mask: np.ndarray) -> int:
    """
    Calculate the projected area of a region

    :param region_mask: mask of a region
    :return: area
    """
    img_proj = project_mask(region_mask)
    props = regionprops(img_proj)
    return props[0].area


def project_mask(region_mask: np.ndarray) -> np.ndarray:
    if len(region_mask.shape) != 3:
        raise ValueError("Input must be a 3D label image.")
    # Project along the first (Z) axis
    img_proj = np.max(region_mask, axis=0)
    return np.asarray(img_proj, dtype=np.uint8)


def create_cell_cyto_masks(
    lbl: np.ndarray, expansion: float, voxel_size: Union[float, tuple] = 1
) -> (np.ndarray, np.ndarray):
    """
    Create cell and cyto masks from the labels.

    Allows expansion for anisotropic data.
    :param lbl: nuclear label mask
    :param expansion: desired expansion in microns
    :param voxel_size: (Z)YX voxel size
    :return: cell mask, cytoplasm mask
    """
    if voxel_size[-1] != voxel_size[-2]:
        raise ValueError(
            f"Voxel size in Y and X must be equal. Got: {voxel_size[-2:]}"
        )
    # skimage has anisotropic expand labels from v0.23.0 on
    # (also requires scipy>=1.8, but I don't think this will be a problem)
    pbr = progress(total=2)
    pbr.set_description("Expanding cells...")
    start = time()
    cells = cell_expansion(lbl, spacing=voxel_size, expansion=expansion)
    pbr.update(1)
    pbr.set_description("Creating cytoplasm...")
    print("Creating cells took:", time() - start)
    start = time()
    # create cyto mask
    cyto = np.subtract(cells, lbl)
    pbr.update(2)
    print("Creating cytoplasm took:", time() - start)
    pbr.close()
    return cells, cyto


def cell_expansion(
    label_image: np.ndarray,
    spacing: Union[float, tuple] = 1,
    expansion: float = 1,
) -> np.ndarray:
    """
    Basically skimage's expand_labels.

    But since anisotropic expansion is only available since skimage v0.23.0,
    re-implement it here: copied from:
    https://github.com/scikit-image/scikit-image/blob/v0.25.1/skimage/segmentation/_expand_labels.py
    :param label_image:
    :param spacing: usually a tuple of the voxel-size,
                    used to calculate the distance map with anisotropy
    :param expansion: distance in microns (if the spacing tuple is in microns)
    :return:
    """
    if check_skimage_version(0, 22, 9):
        return expand_labels(label_image, distance=expansion, spacing=spacing)
    # Re-implementation
    from scipy.ndimage import distance_transform_edt

    distances, nearest_label_coords = distance_transform_edt(
        label_image == 0, sampling=spacing, return_indices=True
    )
    labels_out = np.zeros_like(label_image)
    dilate_mask = distances <= expansion
    # build the coordinates to find the nearest labels,
    # in contrast to 'cellprofiler' this implementation supports label arrays
    # of any dimension
    masked_nearest_label_coords = [
        dimension_indices[dilate_mask]
        for dimension_indices in nearest_label_coords
    ]
    nearest_labels = label_image[tuple(masked_nearest_label_coords)]
    labels_out[dilate_mask] = nearest_labels
    return labels_out


def rename_dict_keys(d: dict, prefix: str, exclude: str = "label") -> dict:
    """
    Rename the keys of a dictionary with a prefix.

    E.g. 'Intensity' becomes 'Nucleus: Intensity'
    :param d: dictionary
    :param prefix: str prefix to use
    :param exclude: str, single dict key to exclude from renaming
    :return: dict
    """
    return_dict = {}
    for k, v in d.items():
        # Add exclude-key without renaming
        if k == exclude:
            return_dict[k] = v
        else:
            return_dict[f"{prefix}: {k}"] = v
    return return_dict


def merge_dict(dict1: dict, dict2: dict, exclude: str = "label") -> dict:
    """
    Merge dict2 into dict1.

    Intended to merge 2 regionprop tables.
    Allows for exclusion of one key-value pair, i.e. the label entry
    :param dict1: first dict
    :param dict2: second dict
    :param exclude: key from second dict to exclude
    :return: merged dict
    """
    if exclude not in dict1:
        raise KeyError(
            f'Expected "{exclude}" in first dictionary, but was not found.'
        )
    if exclude not in dict2:
        raise KeyError(
            f'Expected "{exclude}" in second dictionary, but was not found.'
        )
    # Add key-value pairs to first dict
    for k, v in dict2.items():
        if k == exclude:
            continue
        if k in dict1:
            raise KeyError(f"The dictionary already contains the key {k}.")
        dict1[k] = v
    return dict1
