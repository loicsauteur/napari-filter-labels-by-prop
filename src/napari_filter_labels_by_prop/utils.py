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

    # TODO remove: comparing to multiprocessing options
    # start = time.time()
    # result = remove_indices2(img, labels)
    # print('time multiprocess =', time.time() - start)
    return copy


def find_indices(label, img):
    """
    Function to find indices in image that correspond to a label.

    :param label: int label of interest
    :param img: image
    :return: boolean array of same size as image (True where == label)
    """
    indices = img == label
    return indices


def remove_indices(img: np.ndarray, labels: List[int]):
    """
    Multiprocessing for removing labels.
    Parallelise creation of index arrays, where True for a given label.
    Stacks the labels, then projects them, for setting the label indices to 0.

    Problem: large images leads to out of memory problems.

    :param img: label image
    :param labels: list of labels to remove
    :return: copy of label image with desired labels removed
    """
    copy = np.ndarray.copy(img)
    labels.remove(None)
    labels.remove(0)
    # Fixme if only one label, special case

    with multiprocessing.Pool() as pool:
        result = pool.map(partial(find_indices, img=copy), labels)
    # get the result as a stack of images
    result = np.asarray(result)
    # Max Project it, i.e. single image of booleans for where labels of interest are
    result = np.max(result, axis=0)
    # Set the positions to 0
    copy[result] = 0
    return copy


def remove_indices2(img: np.ndarray, labels: List[int]):
    """
    Multiprocessing modification of the function above.
    Idea is to split the list of labels into sub-chunks for multi-processing.

    Problem: takes longer than single-process.

    :param img: label image
    :param labels: list of labels to remove
    :return: copy of label image with desired labels removed
    """
    copy = np.ndarray.copy(img)
    labels.remove(0)
    labels.remove(None)
    chunk_size = multiprocessing.cpu_count()
    list_of_labels = np.array_split(
        labels, len(labels) // chunk_size + (len(labels) % chunk_size != 0)
    )
    # print("list_of_labels:", list_of_labels)

    for chunk in progress(list_of_labels):
        with multiprocessing.Pool() as pool:
            result = pool.map(partial(find_indices, img=copy), chunk)
        result = np.asarray(result)
        result = np.max(result, axis=0)
        copy[result] = 0
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
