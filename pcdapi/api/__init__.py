''' PCIC PCDS backend API module

.. moduleauthor:: James Hiebert <hiebert@uvic.ca>

'''

import inspect

from json import dumps
from werkzeug.wrappers import BaseResponse as Response
from flask import request

from pcdapi.api.stations import stations
from pcdapi.api.monthly_climo import monthly_climo
from pcdapi.api.seasonal_climo import seasonal_climo

methods = {
    'stations': stations,
    'monthly_climo': monthly_climo,
    'seasonal_climo': seasonal_climo
}

__all__ = list(methods.keys()) + ['call']

def call(session, request_type):
    '''Extracts request query parameters, checks for required arguments
       and delegates to helper functions to fetch the results from
       storage

       Args:
          session (sqlalchemy.orm.session.Session): A database Session object
          request_type(str): name of the API endpoint to call

       Returns:
          werkzeug.wrappers.Response.  A JSON encoded response object
    '''

    try:
        func = methods[request_type]
    except KeyError:
        return Response("Bad Request", status=400)

    # Check that required args are included in the query params
    required_params = set(get_required_args(func)).difference(['sesh'])
    provided_params = set(request.args.keys())
    optional_params = set(get_keyword_args(func))
    if required_params.difference(provided_params):
        return Response("Missing query params", status=400)

    # FIXME: Sanitize input
    args = { key: request.args.get(key) for key in required_params }
    kwargs = { key: request.args.get(key) for key in optional_params if request.args.get(key) is not None }
    args.update(kwargs)
    return Response(
        # Note: all arguments to the delgate functions are necessarily strings
        # at this point, since they're all coming through the URL query
        # parameters
        dumps(func(session, **args)),
        content_type='application/json'
    )

# from http://stackoverflow.com/questions/196960/can-you-list-the-keyword-arguments-a-python-function-receives
def get_required_args(func):
    args, _, _, defaults = inspect.getargspec(func)
    if defaults:
        args = args[:-len(defaults)]
    return args   # *args and **kwargs are not required, so ignore them.

def get_keyword_args(func):
    args, _, _, defaults = inspect.getargspec(func)
    if defaults:
        return args[-len(defaults):]
    else:
        return []
