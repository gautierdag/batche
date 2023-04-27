import inspect
from functools import wraps
from typing import Callable, List, Optional, TypeVar, Any
from collections import OrderedDict

from pydantic import ValidationError, parse_obj_as

R = TypeVar("R")

batche_cache: OrderedDict[Any, List[R]] = OrderedDict()


def is_list_annotation(annotation: Any):
    if annotation is list or (
        hasattr(annotation, "__origin__") and issubclass(list, annotation.__origin__)
    ):
        return True
    return False


def cache_batch_variable(
    batch_variable_name: Optional[str] = None, max_size: Optional[int] = None
):
    def internal_cache_batch_decorator(
        func: Callable[..., List[R]]
    ) -> Callable[..., List[R]]:
        # validate batch_func
        function_function_argspec = inspect.getfullargspec(func)
        if batch_variable_name is not None:
            assert (
                batch_variable_name in function_function_argspec.args
            ), f"{batch_variable_name} must be a valid argument of the batch function"

            batch_arg_annotations = function_function_argspec.annotations.get(
                batch_variable_name
            )
            if batch_arg_annotations:
                assert is_list_annotation(
                    batch_arg_annotations
                ), f"{batch_variable_name} annotation must be a list of hashable objects"

        return_annotation = function_function_argspec.annotations.get("return")
        if return_annotation:
            assert is_list_annotation(
                return_annotation
            ), "return annotation must be a list"

        @wraps(func)
        def batch_function_wrapper(*args, **kwargs):
            args = list(args)
            in_args = False
            for arg_index, arg in enumerate(args):
                try:
                    batch = parse_obj_as(
                        func.__annotations__.get(batch_variable_name), arg
                    )
                    in_args = True
                    break
                except ValidationError:
                    continue
            else:
                batch = kwargs.get(batch_variable_name)
                assert (
                    batch is not None
                ), f"{batch_variable_name} must be a valid argument of the batch function"
                batch = parse_obj_as(
                    func.__annotations__.get(batch_variable_name), batch
                )

            # new_batch will contain only the items that are not in cache
            new_batch, new_indices = [], []

            # initialize predictions with empty lists
            predictions = [[] for _ in range(len(batch))]

            for i, batch_item in enumerate(batch):
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
            assert len(out) == len(
                new_batch
            ), "batch function must return a list of predictions of the same length as the batch"

            for i, prediction in zip(new_indices, out):
                predictions[i] = prediction
                batche_cache[batch[i]] = prediction

            return predictions

        return batch_function_wrapper

    return internal_cache_batch_decorator