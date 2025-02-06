import numpy as np
import numpy.testing as nt
import pytest

import napari_filter_labels_by_prop.utils as uts


def test_remove_labels():
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
    labels_to_remove = {
        1: 1,
        2: 0,
        3: 3,
        4: 0,
        5: 5,
    }
    result = uts.remove_labels(array, labels_to_remove)
    # Check that the result is as expected
    nt.assert_array_equal(
        result,
        expected,
        err_msg="Error testing removing labels with map_array.",
    )
    # Check that the output is not the same as the input
    with nt.assert_raises(AssertionError):
        nt.assert_array_equal(array, result)


@pytest.mark.skip(reason="Deprecated")
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
    # print(array.shape, array.dtype)
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


@pytest.mark.skip(reason="Deprecated")
def test_remove_indices():
    """
    @Deprecated

    :return:
    """
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
# test_remove_labels()
