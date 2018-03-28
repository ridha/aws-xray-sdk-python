import pytest
from .util import get_new_stubbed_recorder


xray_recorder = get_new_stubbed_recorder()
xray_recorder.configure(sampling=False)


def test_subsegment_parenting():

    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    xray_recorder.end_subsegment('name')
    assert xray_recorder.get_trace_entity() is segment

    subsegment1 = xray_recorder.begin_subsegment('name1')
    subsegment2 = xray_recorder.begin_subsegment('name2')

    assert subsegment2.parent_id == subsegment1.id
    assert subsegment1.parent_id == segment.id
    assert subsegment.parent_id == xray_recorder.current_segment().id

    xray_recorder.end_subsegment()
    assert not subsegment2.in_progress
    assert subsegment1.in_progress
    assert xray_recorder.current_subsegment().id == subsegment1.id

    xray_recorder.end_subsegment()
    assert not subsegment1.in_progress
    assert xray_recorder.get_trace_entity() is segment


def test_subsegments_streaming():
    xray_recorder.configure(streaming_threshold=10)
    segment = xray_recorder.begin_segment('name')
    for i in range(0, 11):
        xray_recorder.begin_subsegment(name=str(i))
    for i in range(0, 1):
        # subsegment '10' will be streamed out upon close
        xray_recorder.end_subsegment()

    assert segment.get_total_subsegments_size() == 10
    assert xray_recorder.current_subsegment().name == '9'


def test_capture_not_suppress_exception():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='LOG_ERROR')

    @xray_recorder.capture()
    def buggy_func():
        return 1 / 0

    with pytest.raises(ZeroDivisionError):
        buggy_func()


def test_capture_not_swallow_return():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='LOG_ERROR')
    value = 1

    @xray_recorder.capture()
    def my_func():
        return value

    actual = my_func()
    assert actual == value
