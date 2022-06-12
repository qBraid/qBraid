"""
Unit tests for enums defined in the qbraid device layer.

"""
import pytest

from qbraid.devices.enums import JobStatus, is_status_final, status_from_raw

status_data = [
    (JobStatus.INITIALIZING, False),
    (JobStatus.QUEUED, False),
    (JobStatus.RUNNING, False),
    (JobStatus.CANCELLING, False),
    (JobStatus.CANCELLED, True),
    (JobStatus.COMPLETED, True),
    (JobStatus.FAILED, True),
    (JobStatus.UNKNOWN, False),
]


@pytest.mark.parametrize("status_tuple", status_data)
def test_is_status_final(status_tuple):
    """Test identifying job status objects that are in final state"""
    status_obj, final_expected = status_tuple
    status_str = status_obj.raw()
    final_obj = is_status_final(status_obj)
    final_str = is_status_final(status_str)
    assert final_obj == final_expected
    assert final_str == final_expected


@pytest.mark.parametrize("status", [0, {}, []])
def test_is_status_final_error(status):
    """Test raiseing exception while checking if job status is final"""
    with pytest.raises(TypeError):
        is_status_final(status)


@pytest.mark.parametrize("status_tuple", status_data)
def test_status_from_raw(status_tuple):
    """Test converting str status representation to JobStatus object."""
    status_obj, _ = status_tuple
    status_str = status_obj.raw()
    status_obj_test = status_from_raw(status_str)
    assert status_obj == status_obj_test


@pytest.mark.parametrize("status", ["INITIIZING", "QUDEUED", "CANCELLLED"])
def test_status_from_raw_error(status):
    """Test raising exception while converting invalid str status representation."""
    with pytest.raises(ValueError):
        status_from_raw(status)
