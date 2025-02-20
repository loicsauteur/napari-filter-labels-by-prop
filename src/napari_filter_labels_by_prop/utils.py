from typing import Dict, List

import numpy as np
from napari.utils import progress
from skimage.measure import label, regionprops
from skimage.util import map_array


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
    :param relabel: whether to relabel the new image or not. Default is False.
    :return: new label image with labels removed
    """
    in_vals = np.array(list(label_map.keys()), dtype=int)
    out_vals = np.array(list(label_map.values()), dtype=int)
    new_labels = map_array(
        input_arr=img, input_vals=in_vals, output_vals=out_vals
    )
    if relabel:
        new_labels = label(new_labels)
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
    # if circularity == float('inf'):
    #    print(f'found circ=inf for area={props[0].area} and perimeter={props[0].perimeter}, number of objects: {len(props)}')
    #    if props[0].area < 10:
    #        return 2000.0
    # if circularity > 1:
    #    print(
    #        f'found circ={circularity} for area={props[0].area} and perimeter={props[0].perimeter} perimeter_crofton={props[0].perimeter_crofton}, conv_area={props[0].area_convex}')
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
