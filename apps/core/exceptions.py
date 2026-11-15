from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
   
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': _get_error_type(response.status_code),
            'message': _get_error_message(response.status_code, response.data),
            'details': response.data,
            'status_code': response.status_code
        }
        response.data = custom_response_data
    else:
        # Handle unexpected errors (500 Internal Server Error)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        custom_response_data = {
            'success': False,
            'error': 'server_error',
            'message': 'An unexpected error occurred. Please try again later.',
            'details': str(exc) if settings.DEBUG else None,
            'status_code': 500
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


def _get_error_type(status_code):
    
    error_types = {
        400: 'validation_error',
        401: 'authentication_error',
        403: 'permission_denied',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'too_many_requests',
        500: 'server_error',
    }
    return error_types.get(status_code, 'error')


def _get_error_message(status_code, data):
    
    messages = {
        400: 'The request data is invalid. Please check your input.',
        401: 'Authentication credentials were not provided or are invalid.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        405: 'This HTTP method is not allowed for this endpoint.',
        409: 'The request conflicts with the current state of the server.',
        429: 'Too many requests. Please slow down.',
        500: 'An unexpected error occurred on the server.',
    }
    return messages.get(status_code, 'An error occurred.')

