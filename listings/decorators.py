from functools import wraps
from rest_framework.response import Response


def swagger_safe(view_func):
    """Decorator to handle Swagger schema generation safely"""

    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return Response()
        return view_func(self, request, *args, **kwargs)

    return wrapped_view
