import multiprocessing
from functools import partial
from typing import List

import numpy as np
from napari.utils import progress


def remove_label_objects(
    img: np.ndarray, labels: List[int], n_total_labels: int = None
) -> np.ndarray:
    """
    Function to remove label items from image.

    :param img: label image
    :param labels: List of label to remove. Usually contains None & 0
    :param n_total_labels: total labels in image, currently unused
    :return: new label image
    """
    # Todo find a way to invert labels to remove,
    #  ie. when there is more than total/2
    copy = np.ndarray.copy(img)
    for label in progress(labels):

        if label is not None and label != 0:
            # find indeces where equal label
            a = copy == label
            # set image where indeces true to 0
            copy[a] = 0
    return copy


def remove_objects(
    img: np.ndarray,
    labels: List[int],
) -> np.ndarray:
    """
    @Deprecated
    Try with multiprocessing + np.where.

    Problem is it takes longer than a loop.

    :param img: ndarray
    :param labels: labels to remove
    :return:
    """

    # Create copy of input array
    copy = np.ndarray.copy(img)

    # TODO if n_objects / 2 < len(labels) ?? can I invert it somehow??
    with multiprocessing.Pool() as pool:
        result = pool.map(partial(remove_object, img=copy), labels)
    # result is a list of objects... not sure what do to with it.
    return result


def remove_single_object(label: int, img: np.ndarray):
    """
    @Deprecated
    Function for np.wherer to use for multiprocessing.

    :param label: label number
    :param img: ndarray
    :return:
    """
    return np.where(img == label, 0, img)


def remove_object(label: int, img: np.ndarray):
    """
    @Deprecated
    Function for mulitprocessing- removing objects by indexes.

    :param label: label item of interest
    :param img: ndarray
    :return: modified input image
    """
    a = img == label
    img[a] = 0


def get_indeces(label: int, img: np.ndarray):
    """
    @Deprecated
    Find indeces where a label is present:

    :param label: label of interst
    :param img: ndarray
    :return: boolean ndarray
    """
    a = img == label
    # print('a=', a)
    # print('len a:', len(a), 'with label=', label)
    return a


def remove_objects_by_indices(img: np.ndarray, labels: List[int]):
    """
    @Deprecated
    Multiprocessing loop to get a list indeces for labels.
    Then sets them to 0.
    Problem: takes longer than a loop.

    :param img: ndarray
    :param labels: list of labels
    :return: ndarray with label items set to 0
    """
    labels_ = labels.copy()
    labels_.remove(0)
    labels_.remove(None)
    copy = np.ndarray.copy(img)
    with multiprocessing.Pool() as pool:
        result = pool.map(partial(get_indeces, img=copy), labels_)

    # print(result)
    # print()
    # print(len(result))
    for i in result:
        copy[i] = 0
