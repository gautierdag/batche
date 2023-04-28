from typing import List, Tuple
from unittest.mock import MagicMock

import pytest

from batche import cache_batch_variable
from batche.batche import BatcheException


def test_cache_decorator_success():
    @cache_batch_variable(batch_variable_name="values")
    def sum_values(values: List[Tuple[int, int, int]]) -> List[int]:
        return [sum(value) for value in values]

    result = sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    assert result == [6, 15, 24]


def test_cache_decorator_with_invalid_argument():
    with pytest.raises(
        BatcheException,
        match="invalid_arg must be a valid argument of the batch function",
    ):

        @cache_batch_variable("invalid_arg")
        def sum_values(values: List[int]) -> List[int]:
            return [sum(value) for value in values]

        sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_cache_decorator_with_invalid_annotation():
    with pytest.raises(
        BatcheException, match="values annotation must be a list of hashable objects"
    ):

        @cache_batch_variable("values")
        def sum_values(values: int) -> List[int]:
            return [sum(value) for value in values]

        sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_cache_decorator_with_invalid_return_annotation():
    with pytest.raises(BatcheException, match="return annotation must be a list"):

        @cache_batch_variable("values")
        def sum_values(values: List[int]) -> int:
            return sum(values)

        sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_cache_decorator_with_missing_batch_variable():
    with pytest.raises(
        BatcheException, match="values must be a valid argument of the batch function"
    ):

        @cache_batch_variable("values")
        def sum_values() -> List[int]:
            return []

        sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_cache_decorator_separate_caches():
    sum_values_mock = MagicMock(
        side_effect=lambda values: [sum(value) for value in values]
    )

    @cache_batch_variable("values")
    def sum_values_wrapped(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    @cache_batch_variable("values")
    def sum_values_wrapped_alt(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    # First call to populate the cache
    sum_values_wrapped([(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    assert sum_values_mock.call_count == 1

    # Second call with overlapping inputs, should not use cache since it's a different function
    sum_values_wrapped_alt([(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    assert sum_values_mock.call_count == 2


def test_cache_decorator_avoid_unnecessary_calls():
    sum_values_mock = MagicMock(
        side_effect=lambda values: [sum(value) for value in values]
    )

    @cache_batch_variable("values")
    def sum_values_wrapped(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    # First call to populate the cache
    sum_values_wrapped([(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    assert sum_values_mock.call_count == 1

    # Second call with overlapping inputs, should use cache and call the function
    sum_values_wrapped([(1, 2, 3), (10, 11, 12)])
    assert sum_values_mock.call_count == 2
    sum_values_mock.assert_called_with([(10, 11, 12)])

    # Third call with old inputs, should not call the function
    sum_values_wrapped([(1, 2, 3), (10, 11, 12)])
    assert sum_values_mock.call_count == 2


def test_lru_cache_low_maxsize():
    sum_values_mock = MagicMock(
        side_effect=lambda values: [sum(value) for value in values]
    )

    @cache_batch_variable("values", maxsize=1)
    def sum_values_wrapped(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    # First call to populate the cache
    sum_values_wrapped([(1, 2, 3), (4, 5, 6)])
    assert sum_values_mock.call_count == 1

    # Second call with overlapping inputs, should use cache and call the function
    sum_values_wrapped([(1, 2, 3), (10, 11, 12)])
    assert sum_values_mock.call_count == 2

    # Third call with old inputs
    sum_values_wrapped([(1, 2, 3)])
    assert sum_values_mock.call_count == 3


def test_lru_cache_high_maxsize():
    sum_values_mock = MagicMock(
        side_effect=lambda values: [sum(value) for value in values]
    )

    @cache_batch_variable("values", maxsize=128)
    def sum_values_wrapped_alt(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    # First call to populate the cache
    sum_values_wrapped_alt([(1, 2, 3), (4, 5, 6)])
    assert sum_values_mock.call_count == 1

    # Second call with overlapping inputs, should use cache and call the function
    sum_values_wrapped_alt([(1, 2, 3), (10, 11, 12)])
    assert sum_values_mock.call_count == 2

    # Third call with old inputs
    sum_values_wrapped_alt([(1, 2, 3)])
    assert sum_values_mock.call_count == 2


def test_subfunction_returns_incorrect_length():
    with pytest.raises(
        BatcheException,
        match="batch function must return a list of predictions of the same length as the batch",
    ):
        sum_values_mock = MagicMock(side_effect=lambda values: [5] * 5)

        @cache_batch_variable("values", maxsize=128)
        def sum_values(values: List[Tuple[int, int, int]]) -> List[int]:
            return sum_values_mock(values)

        sum_values([(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_missing_batch_variable():
    with pytest.raises(
        BatcheException, match="values must be a valid argument of the batch function"
    ):
        sum_values_mock = MagicMock(side_effect=lambda x: [5] * 5)

        @cache_batch_variable("values", maxsize=128)
        def sum_values(**kwargs) -> List[int]:
            return sum_values_mock(kwargs["values"])

        sum_values(fake=[(1, 2, 3), (4, 5, 6), (7, 8, 9)])


def test_no_annotations_kwargs_usage():
    @cache_batch_variable("values")
    def sum_values_wrapped_alt(values):
        return [sum(value) for value in values]

    result = sum_values_wrapped_alt(values=[(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    assert result == [6, 15, 24]


# def test_no_annotations_kwargs_usage():

#     with pytest.raises(
#         BatcheException, match="values must be a valid argument of the batch function"
#     ):
#         @cache_batch_variable("values")
#         def sum_values_wrapped_alt(values):
#             return [sum(value) for value in values]

#     result = sum_values_wrapped_alt([(1, 2, 3), (4, 5, 6), (7, 8, 9)])
#     assert result == [6, 15, 24]
