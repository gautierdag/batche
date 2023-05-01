import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .lrucache import LRUCache

R = TypeVar("R")


class BatcheException(Exception):
    pass


def is_list_annotation(annotation: Any):
    """
    Check if annotation is a list or a generic list
    """
    return annotation is list or (
        hasattr(annotation, "__origin__") and issubclass(list, annotation.__origin__)
    )


def validate_function_annotations(
    func: Callable[..., List[Any]], batch_variable_name: str
) -> int:
    """
    Validate that the batch function has the correct annotations on the batch variable and return value
    Batch variable must be a list of hashable objects
    Return value must be a list of Any type

    If annotations are not provided then ignores validation
    """
    # validate batch_func
    function_argspec = inspect.getfullargspec(func)
    index = -1

    # validate batch_variable_name is a valid argument
    if (
        batch_variable_name not in function_argspec.args
        and function_argspec.varkw is None
    ):
        raise BatcheException(
            f"{batch_variable_name} must be a valid argument of the batch function"
        )

    # get index of batch_variable argument
    if batch_variable_name in function_argspec.args:
        index = function_argspec.args.index(batch_variable_name)

    # validate batch_arg annotation must be list
    batch_arg_annotations = function_argspec.annotations.get(batch_variable_name)
    if batch_arg_annotations and not is_list_annotation(batch_arg_annotations):
        raise BatcheException(
            f"{batch_variable_name} annotation must be a list of hashable objects"
        )

    # validate return annotation must be list
    return_annotation = function_argspec.annotations.get("return")
    if return_annotation and not is_list_annotation(return_annotation):
        raise BatcheException("return annotation must be a list")

    return index


def cache_batch_variable(batch_variable_name: str, maxsize: Optional[int] = None):
    batche_cache: Dict[Any, List[R]] = {}
    if maxsize is not None:
        batche_cache = LRUCache(maxsize=maxsize)

    def internal_cache_batch_decorator(
        func: Callable[..., List[R]]
    ) -> Callable[..., List[R]]:
        arg_index = validate_function_annotations(
            func, batch_variable_name=batch_variable_name
        )

        @wraps(func)
        def batch_function_wrapper(*args, **kwargs):
            args = list(args)
            in_args = False  # tracks where the batch_variable is (in args or kwargs)

            # check if batch_variable is in kwargs
            batch_variable = kwargs.get(batch_variable_name)
            if batch_variable is None:
                if arg_index < 0 or arg_index >= len(args):
                    raise BatcheException(
                        f"{batch_variable_name} must be a valid argument of the batch function"
                    )
                batch_variable = args[arg_index]
                in_args = True

            # new_batch will contain only the items that are not in cache
            new_batch, new_indices = [], []

            # initialize predictions with empty lists
            predictions = [[] for _ in range(len(batch_variable))]

            for i, batch_item in enumerate(batch_variable):
                if batch_item in batche_cache:
                    predictions[i] = batche_cache[batch_item]
                else:
                    new_batch.append(batch_item)
                    new_indices.append(i)

            # if all items are in cache, return
            if len(new_batch) == 0:
                return predictions

            if in_args:
                args[arg_index] = new_batch
            else:
                kwargs[batch_variable_name] = new_batch

            # call the function with the new batch
            out = func(*args, **kwargs)

            # validate that the function returns a list of the same length as the new batch
            if len(out) != len(new_batch):
                raise BatcheException(
                    "batch function must return a list of predictions of the same length as the batch"
                )

            # update the cache and outputs
            for i, prediction in zip(new_indices, out):
                predictions[i] = prediction
                batche_cache[batch_variable[i]] = prediction

            return predictions

        return batch_function_wrapper

    return internal_cache_batch_decorator
