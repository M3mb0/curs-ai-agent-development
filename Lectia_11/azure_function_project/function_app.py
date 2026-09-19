import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Returns a greeting message, using an optional name from the
    request's query parameters.

    Args:
        req: the incoming HTTP request, containing an optional
            "name" query parameter

    Returns:
        An HTTP response with the greeting text
    """
    name = req.params.get('name', 'World')
    return func.HttpResponse(f"Hello, {name}!")