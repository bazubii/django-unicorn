from unittest.mock import MagicMock

from django_unicorn.components import UnicornView
from django_unicorn.utils import (
    CacheableComponent,
    generate_checksum,
    get_method_arguments,
    get_type_hints,
    is_non_string_sequence,
    sanitize_html,
)


def test_generate_checksum_bytes(settings):
    settings.SECRET_KEY = "asdf"

    expected = "TfxFqcQL"
    actual = generate_checksum(b'{"name": "test"}')

    assert expected == actual


def test_generate_checksum_str(settings):
    settings.SECRET_KEY = "asdf"

    expected = "TfxFqcQL"
    actual = generate_checksum('{"name": "test"}')

    assert expected == actual


def test_get_method_arguments():
    def test_func(input_str):
        return input_str

    expected = [
        "input_str",
    ]
    actual = get_method_arguments(test_func)
    assert actual == expected


def test_get_method_arguments_with_type_annotation():
    def test_func(input_str: str):
        return input_str

    expected = [
        "input_str",
    ]
    actual = get_method_arguments(test_func)
    assert actual == expected


def test_get_type_hints():
    def test_func(input_str: str):
        return input_str

    expected = {"input_str": str}
    actual = get_type_hints(test_func)
    assert actual == expected


def test_get_type_hints_missing_type_hints():
    def test_func(input_str):
        return input_str

    expected = {}
    actual = get_type_hints(test_func)
    assert actual == expected


def test_sanitize_html():
    expected = '{"id":"abcd123","name":"text-inputs","key":"asdf","data":{"name":"World","testing_thing":"Whatever \\u003C/script\\u003E \\u003Cscript\\u003Ealert(\'uh oh\')\\u003C/script\\u003E"},"calls":[],"hash":"hjkl"}'
    data = '{"id":"abcd123","name":"text-inputs","key":"asdf","data":{"name":"World","testing_thing":"Whatever </script> <script>alert(\'uh oh\')</script>"},"calls":[],"hash":"hjkl"}'
    actual = sanitize_html(data)
    assert actual == expected


class FakeComponent(UnicornView):
    pass


def test_cacheable_component_request_is_none_then_restored():
    component = FakeComponent(component_id="asdf123498", component_name="hello-world")
    request = component.request = MagicMock()
    assert component.request

    with CacheableComponent(component):
        assert component.request is None

    assert component.request == request


def test_cacheable_component_extra_context_is_none_then_restored():
    component = FakeComponent(component_id="asdf123499", component_name="hello-world")
    extra_context = component.extra_context = MagicMock()
    assert component.extra_context

    with CacheableComponent(component):
        assert component.extra_context is None

    assert component.extra_context == extra_context


def test_cacheable_component_parents_have_request_restored():
    component = FakeComponent(component_id="asdf123498", component_name="hello-world")
    component2 = FakeComponent(
        component_id="asdf123499", component_name="hello-world", parent=component
    )
    component3 = FakeComponent(
        component_id="asdf123500", component_name="hello-world", parent=component2
    )
    request = MagicMock()
    extra_content = "extra_content"
    for c in [component, component2, component3]:
        c.request = request
        c.extra_context = extra_content

    with CacheableComponent(component3):
        assert component.request is None
        assert component2.request is None
        assert component3.request is None
        assert component.extra_context is None
        assert component2.extra_context is None
        assert component3.extra_context is None

    assert component.request == request
    assert component2.request == request
    assert component3.request == request
    assert component.extra_context == extra_content
    assert component2.extra_context == extra_content
    assert component3.extra_context == extra_content


def test_restore_cached_component_children_have_request_set():
    component = FakeComponent(component_id="asdf123498", component_name="hello-world")
    component2 = FakeComponent(component_id="asdf123499", component_name="hello-world")
    component3 = FakeComponent(component_id="asdf123500", component_name="hello-world")
    component4 = FakeComponent(component_id="asdf123501", component_name="hello-world")
    component3.children.append(component4)
    component.children.extend([component2, component3])
    request = MagicMock()
    extra_content = "extra_content"
    for c in [component, component2, component3, component4]:
        c.request = request
        c.extra_context = extra_content

    with CacheableComponent(component):
        assert component.request is None
        assert component2.request is None
        assert component3.request is None
        assert component4.request is None
        assert component.extra_context is None
        assert component2.extra_context is None
        assert component3.extra_context is None
        assert component4.extra_context is None

    assert component.request == request
    assert component2.request == request
    assert component3.request == request
    assert component4.request == request
    assert component.extra_context == extra_content
    assert component2.extra_context == extra_content
    assert component3.extra_context == extra_content
    assert component4.extra_context == extra_content


def test_is_non_string_sequence_list():
    assert is_non_string_sequence(
        [
            "",
        ]
    )


def test_is_non_string_sequence_tuple():
    assert is_non_string_sequence(("",))


def test_is_non_string_sequence_set():
    assert is_non_string_sequence(
        {
            "",
        }
    )


def test_is_non_string_sequence_string():
    assert not is_non_string_sequence("")


def test_is_non_string_sequence_bytes():
    assert not is_non_string_sequence(b"")
