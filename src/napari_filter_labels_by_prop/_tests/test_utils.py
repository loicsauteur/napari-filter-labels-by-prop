import numpy as np
import numpy.testing as nt

import napari_filter_labels_by_prop.utils as uts


def test_remove_label_objects():
    # Fixme: maybe I should have the same dtype as when loaded from napari?
    array = [
        [
            [1, 0, 0, 0, 0],
            [0, 2, 2, 0, 5],
            [0, 4, 4, 0, 5],
            [0, 4, 4, 0, 5],
        ],
        [
            [1, 0, 2, 3, 5],
            [1, 0, 2, 3, 5],
            [0, 0, 4, 0, 5],
            [4, 4, 4, 0, 0],
        ],
    ]
    array = np.asarray(array)
    print(array.shape, array.dtype)
    expected = [
        [
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 5],
            [0, 0, 0, 0, 5],
            [0, 0, 0, 0, 5],
        ],
        [
            [1, 0, 0, 3, 5],
            [1, 0, 0, 3, 5],
            [0, 0, 0, 0, 5],
            [0, 0, 0, 0, 0],
        ],
    ]
    expected = np.asarray(expected)

    out = uts.remove_label_objects(
        array,
        [0, None, 2, 4],
    )

    nt.assert_array_equal(
        out, expected, err_msg="Error when testing removing label objects."
    )


def test_find_indices():
    pass


def test_remove_indices():
    img = [[1, 0, 0, 0, 0], [0, 2, 2, 0, 0], [0, 3, 3, 3, 0], [5, 5, 5, 5, 5]]
    img = np.asarray(img)
    # Labels to remove
    labels = [None, 0, 2, 3]
    expected = [
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [5, 5, 5, 5, 5],
    ]
    expected = np.asarray(expected)
    r = uts.remove_indices(img, labels)
    nt.assert_array_equal(expected, r, err_msg="Removing labels failed.")


# if __name__ == "__main__":
# test_remove_label_objects()
# test_remove_indices()
