from typing import List, Tuple
from unittest.mock import MagicMock

import pytest

from batche import batche_cache, cache_batch_variable


def test_cache_decorator_success():
    @cache_batch_variable(batch_variable_name="values")
    def sum_values(values: List[Tuple[int, int, int]]) -> List[int]:
        return [sum(value) for value in values]

    result = sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert result == [6, 15, 24]


def test_cache_decorator_with_invalid_argument():
    with pytest.raises(
        AssertionError,
        match="invalid_arg must be a valid argument of the batch function",
    ):

        @cache_batch_variable("invalid_arg")
        def sum_values(values: List[int]) -> List[int]:
            return [sum(value) for value in values]

        sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


def test_cache_decorator_with_invalid_annotation():
    with pytest.raises(
        AssertionError, match="values annotation must be a list of hashable objects"
    ):

        @cache_batch_variable("values")
        def sum_values(values: int) -> List[int]:
            return [sum(value) for value in values]

        sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


def test_cache_decorator_with_invalid_return_annotation():
    with pytest.raises(AssertionError, match="return annotation must be a list"):

        @cache_batch_variable("values")
        def sum_values(values: List[int]) -> int:
            return sum(values)

        sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


def test_cache_decorator_with_missing_batch_variable():
    with pytest.raises(
        AssertionError, match="values must be a valid argument of the batch function"
    ):

        @cache_batch_variable("values")
        def sum_values() -> List[int]:
            return []

        sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


def test_cache_decorator_reuse_cache():
    @cache_batch_variable("values")
    def sum_values(values: List[Tuple[int, int, int]]) -> List[int]:
        return [sum(value) for value in values]

    # First call to populate the cache
    result1 = sum_values([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert result1 == [6, 15, 24]
    assert (1, 2, 3) in batche_cache
    assert (4, 5, 6) in batche_cache
    assert (7, 8, 9) in batche_cache
    assert (10, 11, 12) not in batche_cache

    # Second call with overlapping inputs, should use cache
    result2 = sum_values([[1, 2, 3], [10, 11, 12]])
    assert result2 == [6, 33]
    assert (10, 11, 12) in batche_cache


def test_cache_decorator_avoid_unnecessary_calls():
    # Clear the cache
    batche_cache.clear()

    sum_values_mock = MagicMock(
        side_effect=lambda values: [sum(value) for value in values]
    )

    @cache_batch_variable("values")
    def sum_values_wrapped(values: List[Tuple[int, int, int]]) -> List[int]:
        return sum_values_mock(values)

    # First call to populate the cache
    sum_values_wrapped([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert sum_values_mock.call_count == 1

    # Second call with overlapping inputs, should use cache and call the function
    sum_values_wrapped([[1, 2, 3], [10, 11, 12]])
    assert sum_values_mock.call_count == 2
    sum_values_mock.assert_called_with([(10, 11, 12)])

    # Third call with old inputs, should not call the function
    sum_values_wrapped([[1, 2, 3], [10, 11, 12]])
    assert sum_values_mock.call_count == 2
