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


# if __name__ == "__main__":
# test_remove_label_objects()
