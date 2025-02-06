from typing import Dict, List

import numpy as np
from napari.utils import progress
from skimage.util import map_array


def remove_labels(img: np.ndarray, label_map: Dict[int, int]) -> np.ndarray:
    """
    Returns a new label image wih label removed.

    Uses skimage.util.map_array, which is fast.
    map_array requires a list of input_val = ALL label indices, and
    output_vals, which is a list of same length as input_val and maps,
    the values (e.g. same label value for labels to keep, or 0 for the ones to remove).
    :param img: label image
    :param label_map: dict of {label: [label or 0]}
    :return: new label image with labels removed
    """
    in_vals = np.array(list(label_map.keys()), dtype=int)
    out_vals = np.array(list(label_map.values()), dtype=int)
    return map_array(input_arr=img, input_vals=in_vals, output_vals=out_vals)


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
    for label in progress(labels):
        if label is not None and label != 0:
            # find indices where equal label
            a = copy == label
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
