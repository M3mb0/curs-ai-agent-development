import time

_cache = {}

def fake_expensive_call(text: str) -> str:
    """Simulates a slow, costly API call.

    Args:
        text: the text to process

    Returns:
        A simulated embedding string for the given text
"""
    time.sleep(2)  # simulăm întârzierea reală a unui apel API
    return f"embedding_for_{text}"


def cached_get_embedding(text: str) -> str:
    """Returns a cached result for the text, computing and storing it
    if not already cached.

    Args:
        text: the text to get an embedding for

    Returns:
        The (possibly cached) embedding string for the text
"""
    if text in _cache.keys():
        return _cache[text]
    _cache[text] = fake_expensive_call(text)
    return _cache[text]


def route_by_complexity(task_type: str) -> str:
    """Selects the appropriate model name based on task complexity, for cost efficiency.

    Args:
        task_type: the type of task (e.g. "classification", "reasoning")

    Returns:
        The most cost-effective model name for the given task type
    """
    simple_tasks = ["classification", "routing", "extraction"]
    complex_tasks = ["analysis", "reasoning", "writing"]

    if task_type in simple_tasks:
        return "gemini-3.5-flash-lite"
    elif task_type in complex_tasks:
        return "gemini-3.6-flash"
    return "gemini-3.5-flash-lite"  # implicit, model ieftin, mai sigur decât unul scump


start = time.time()
cached_get_embedding("hello")
print("Primul apel:", time.time() - start, "secunde")

start = time.time()
cached_get_embedding("hello")  # aceeași întrebare
print("Al doilea apel:", time.time() - start, "secunde")

print("-"*50)

print(route_by_complexity("routing"))
print(route_by_complexity("reasoning"))
print(route_by_complexity("unknown_task"))