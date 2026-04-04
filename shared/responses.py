from rest_framework.response import Response
from rest_framework import status as http_status


def success_response(data=None, message="Success", status_code=http_status.HTTP_200_OK):
    return Response(
        {"success": True, "message": message, "data": data},
        status=status_code,
    )


def created_response(data=None, message="Created successfully"):
    return success_response(
        data=data, message=message, status_code=http_status.HTTP_201_CREATED
    )


def error_response(
    message="An error occurred",
    errors=None,
    status_code=http_status.HTTP_400_BAD_REQUEST,
):
    return Response(
        {"success": False, "message": message, "errors": errors},
        status=status_code,
    )


def not_found_response(message="Resource not found"):
    return error_response(message=message, status_code=http_status.HTTP_404_NOT_FOUND)


def unauthorized_response(message="Authentication required"):
    return error_response(message=message, status_code=http_status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message="Permission denied"):
    return error_response(message=message, status_code=http_status.HTTP_403_FORBIDDEN)
