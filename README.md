

[![tests](https://github.com/gautierdag/batche/actions/workflows/test.yml/badge.svg)](https://github.com/gautierdag/batche/actions/workflows/test.yml)
[![image](https://img.shields.io/pypi/v/batche.svg)](https://pypi.python.org/pypi/batche)
[![image](https://img.shields.io/pypi/l/batche.svg)](https://pypi.python.org/pypi/batche)
[![image](https://img.shields.io/pypi/pyversions/batche.svg)](https://pypi.python.org/pypi/batche)

# batche (batch + cache)

`batche` provides a Python decorator analogous to `lru_cache` but for functions that transform list objects.

It helps in reducing computation by caching the outputs of each previously processed input in the batch. The cache is maintained using a dictionary or an LRU (Least Recently Used) Cache, based on the maxsize parameter. If maxsize is not provided, the cache will be a simple dictionary.

This is useful when you have a costly function that takes a batch of items as input and returns a list of predictions. If you call this function multiple times with overlapping batches, the results for the overlapping examples will be fetched from the cache, improving the performance.

## Installation

```bash
pip install batche
```

## Why?

You might be calling an external API or machine learning model that takes a batch of items as input and returns a list of predictions.

However, if you are calling the function with inputs that overlap, you might be wasting computation by calling the function multiple times with the same input examples.


### OPENAI API EXAMPLE

```python
import openai
from batche import cache_batch_variable

@cache_batch_variable(batch_variable_name="batch_items", maxsize=100)
def get_openai_embeddings(batch_items: List[str]) -> List[float]:
    # Costly computation
    response = openai.Embedding.create(
        input="Your text string goes here",
        model="text-embedding-ada-002"
    )
    return [d["embedding"] for d in response['data']]

# api will be called with batch of 2 items and the results will be cached
embeddings_1 = get_openai_embeddings(["hello", "world"])

# api will be called with batch of 1 items ("again"), the results for "hello" will be fetched from the cache
embeddings_2 = get_openai_embeddings(["hello", "again"])

# api will not be called, the embeddigns will be fetched from the cache
embeddings_2 = get_openai_embeddings(["hello", "again"])

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


### Example

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

By default, the cache size is unlimited (uses a dictionary). If you want to limit the cache size, you can use the `maxsize` parameter, this will create an LRU Cache with the specified size.


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
