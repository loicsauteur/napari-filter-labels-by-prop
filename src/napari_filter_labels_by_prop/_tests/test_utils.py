import numpy as np
import numpy.testing as nt
import pytest
from skimage.measure import regionprops, regionprops_table
from skimage.morphology import ball, disk

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
    # expected when relabelling
    expected = [
        [
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 3],
            [0, 0, 0, 0, 3],
            [0, 0, 0, 0, 3],
        ],
        [
            [1, 0, 0, 2, 3],
            [1, 0, 0, 2, 3],
            [0, 0, 0, 0, 3],
            [0, 0, 0, 0, 0],
        ],
    ]
    expected_keep_labels = [
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
    result = uts.remove_labels(array, labels_to_remove, relabel=True)
    # Check that the result is as expected
    nt.assert_array_equal(
        result,
        expected,
        err_msg="Error testing removing labels with map_array & relabelling.",
    )
    # Check that the output is not the same as the input
    with nt.assert_raises(AssertionError):
        nt.assert_array_equal(array, result)
    # Check with the (default) relabel=False option
    nt.assert_array_equal(
        uts.remove_labels(array, labels_to_remove),
        expected_keep_labels,
        err_msg="Error in testing removing labels with map_array & keeping label IDs",
    )


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


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_projected_extra_props():
    radius = 10
    sphere = ball(radius)
    disk_props = regionprops(disk(radius))
    expected_perimeter = disk_props[0].perimeter
    expected_hull = disk_props[0].area_convex
    expected_area = disk_props[0].area

    table = regionprops_table(
        sphere,
        extra_properties=(
            uts.projected_area,
            uts.projected_convex_area,
            uts.projected_circularity,
            uts.projected_perimeter,
        ),
    )

    nt.assert_array_almost_equal(
        table["projected_circularity"],
        [0.9],
        decimal=1,
        err_msg="Projected circularity failed",
    )
    nt.assert_array_equal(
        table["projected_perimeter"],
        [expected_perimeter],
        err_msg="Projected perimeter failed",
    )
    nt.assert_array_equal(
        table["projected_convex_area"],
        [expected_hull],
        err_msg="Projected convex area failed",
    )
    nt.assert_array_equal(
        table["projected_area"],
        [expected_area],
        err_msg="Projected area failed",
    )


if __name__ == "__main__":
    test_remove_labels()
# test_remove_indices()
# test_remove_labels()
