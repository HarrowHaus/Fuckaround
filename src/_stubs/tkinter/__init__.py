"""Headless stub for tkinter — NAM only needs it for its GUI trainer."""
class _Any:
    def __init__(self, *a, **k): pass
    def __call__(self, *a, **k): return _Any()
    def __getattr__(self, k): return _Any()

def __getattr__(name):
    return _Any

TclError = RuntimeError
