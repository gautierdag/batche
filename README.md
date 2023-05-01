

[![tests](https://github.com/gautierdag/batche/actions/workflows/test.yml/badge.svg)](https://github.com/gautierdag/batche/actions/workflows/test.yml)

# batche

`batche` provides a Python decorator that caches the results of a batch function. It helps in reducing computation by caching the outputs for previously processed input batches. The cache is maintained using a dictionary or an LRU (Least Recently Used) Cache, based on the maxsize parameter.

## Installation

```bash
pip install batche
```

## Usage

To use this decorator, simply import it and apply it to a function that takes a batch of items (list) as input and returns a list of predictions. The decorator will cache the results of the function for previously processed items.

```python
from batche import cache_batch_variable

# batch_variable_name (str): The name of the argument in your batch function that holds the input batch list. This is a required parameter.
# maxsize (int, optional): The maximum size of the cache (uses an LRU Cache).
#                          If not provided, the cache used will be a dict.
@cache_batch_variable(batch_variable_name="batch_items", maxsize=100)
def batch_function(batch_items: List[HashableType]) -> List[Any]:
    # Your implementation here
    return expensive_operation(batch_items)
```


## Example

Here is a complete example using the cache_batch_variable decorator:

```python

from cache_batch_decorator import cache_batch_variable

@cache_batch_variable(batch_variable_name="batch_items", maxsize=100)
def batch_function(batch_items: List[str]) -> List[str]:
    # Simulating some heavy computation
    result = [item.upper() for item in batch_items]
    return result

# Test the batch_function
input_batch = ["hello", "world"]

output_batch = batch_function(input_batch)
print(output_batch)
> ['HELLO', 'WORLD']

# Calling the function again with overlapping examples
# The results for the overlapping examples will be fetched from the cache
# The results for the new examples will be computed
input_batch = ["hello", "again",]
output_batch = batch_function(input_batch)
print(output_batch)
> ['HELLO', 'AGAIN']

```

When calling the function with the same input batch again, the results will be fetched from the cache, improving the performance.
Cache Types

By default, the cache size is unlimited (uses a dictionary). If you want to limit the cache size, you can use the `maxsize` parameter. This will create an LRU Cache with the specified size:


# Important Notes

- The decorator checks for correct annotations of the batch function (input and return types should be a list). If annotations are not provided, it skips the validation.

- The input batch variable must contain hashable objects.

- The batch function must return a list of predictions with the same length as the input batch.

- The gains in performance will depend on the size of the input batch and the computation time of the batch function. If the batch function is very fast, the gains will be minimal. This is also only useful if you are calling the batch function with possible duplicate examples multiple times.


# Possible Improvements

- [ ] Add support for multiple batch variables (e.g. batch_items, batch_labels, batch_ids, etc.)
- [ ] Add support for custom cache implementations and hash functions
- [ ] Add run-time annotations validation


# Contributing

Contributions are welcome! Please open an issue if you have any suggestions or improvements.

# License

This project is licensed under the MIT License.
