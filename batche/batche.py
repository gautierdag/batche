import inspect
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic import ValidationError, parse_obj_as

R = TypeVar("R")

class BatcheException(Exception):
    pass

def is_list_annotation(annotation: Any):
    """
    Check if annotation is a list or a generic list
    """
    return (annotation is list or (
        hasattr(annotation, "__origin__") and issubclass(list, annotation.__origin__)
    ))


def validate_function_annotations(func: Callable[..., List[Any]], batch_variable_name: Optional[str] = None)->None:
    """
    Validate that the batch function has the correct annotations on the batch variable and return value
    Batch variable must be a list of hashable objects
    Return value must be a list of Any type

    If annotations are not provided then ignores validation
    """
    # validate batch_func
    function_function_argspec = inspect.getfullargspec(func)
    if batch_variable_name is not None:
        # TODO: don't require annotations if batch_variable_name is provided in kwargs
        if batch_variable_name not in function_function_argspec.args:
            raise BatcheException(f"{batch_variable_name} must be a valid argument of the batch function")

        batch_arg_annotations = function_function_argspec.annotations.get(
            batch_variable_name
        )
        if batch_arg_annotations and not is_list_annotation(batch_arg_annotations):
            raise BatcheException(f"{batch_variable_name} annotation must be a list of hashable objects")

    # validate return annotation must be list
    return_annotation = function_function_argspec.annotations.get("return")
    if return_annotation and not is_list_annotation(return_annotation):
        raise BatcheException("return annotation must be a list")


def cache_batch_variable(
    batch_variable_name: Optional[str] = None, max_size: Optional[int] = None
):
    # @TODO: implement max_size
    batche_cache: Dict[Any, List[R]] = OrderedDict()

    def internal_cache_batch_decorator(
        func: Callable[..., List[R]]
    ) -> Callable[..., List[R]]:
        
        validate_function_annotations(func, batch_variable_name=batch_variable_name)

        @wraps(func)
        def batch_function_wrapper(*args, **kwargs):
            args = list(args)
            in_args = False

            # check if batch_variable is in args or kwargs
            batch_variable = kwargs.get(batch_variable_name)
            if batch_variable is not None:
                batch_variable = parse_obj_as(
                    func.__annotations__.get(batch_variable_name), batch_variable
                )
            else:
                for arg_index, arg in enumerate(args):
                    try:
                        # check if batch_variable meets the annotation provided
                        # NOTE: this will fail if more than one argument
                        # meets the annotation before batch_variable
                        batch_variable = parse_obj_as(
                            func.__annotations__.get(batch_variable_name), arg
                        )
                        in_args = True
                        break
                    except ValidationError:
                        continue
            if batch_variable is None:
                # TODO: Test
                raise BatcheException(f"{batch_variable_name} must be a valid argument of the batch function")

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
            # TODO: Test
            if len(out) != len(new_batch):
                raise BatcheException("batch function must return a list of predictions of the same length as the batch")

            # update the cache and outputs
            for i, prediction in zip(new_indices, out):
                predictions[i] = prediction
                batche_cache[batch_variable[i]] = prediction

            return predictions

        return batch_function_wrapper

    return internal_cache_batch_decorator
