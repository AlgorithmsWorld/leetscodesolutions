from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from structlog.stdlib import BoundLogger

from app.commons.context.req_context import get_logger_from_req, response_with_req_id


class PaymentError(Exception):
    """
    Base exception class. This is base class that can be inherited by
    each business operation layer with corresponding sub error class and
    raise to application layers.
    """

    def __init__(self, error_code: str, error_message: str, retryable: bool):
        """
        Base exception class.

        :param error_code: payin service predefined client-facing error codes.
        :param error_message: friendly error message for client reference.
        :param retryable: identify if the error is retryable or not.
        """
        super(PaymentError, self).__init__(error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.retryable = retryable


class PaymentException(HTTPException):
    """
    Payment external exception class. This is application-level class that can be used
    by each FastAPI router to return error back to client.
    """

    def __init__(
        self,
        http_status_code: int,
        error_code: str,
        error_message: str,
        retryable: bool,
    ):
        """
        External exception class.

        :param http_status_code: http status code
        :param error_code: payin service predefined client-facing error codes.
        :param error_message: friendly error message for client reference.
        :param retryable: identify if the error is retryable or not.
        """
        super().__init__(status_code=http_status_code, detail=error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.retryable = retryable


class PaymentErrorResponseBody(BaseModel):
    """
    Customized payment error http response body.

    :param error_code: payin service predefined client-facing error codes.
    :param error_message: friendly error message for client reference.
    :param retryable: identify if the error is retryable or not.
    """

    error_code: str
    error_message: str
    retryable: bool


def create_payment_error_response_blob(
    status_code: int, resp_blob: PaymentErrorResponseBody
):
    """
    Create customized payment error http response.

    :param status_code: http status code.
    :param resp_blob: PaymentErrorResponseBody object.
    :return:
    """
    # FIXME: this method should be replaced by FASTAPI custom exception handler:
    #        https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
    #        See PaymentException and payment_exception_handler for more information.
    return JSONResponse(status_code=status_code, content=jsonable_encoder(resp_blob))


async def payment_http_exception_handler(
    request: Request, exception: StarletteHTTPException
):
    """
    Payment http exception handler.
    As .PaymentException is a subclass of fastapi.HTTPException,
    we are overriding default FastAPI http_exception_handler here in a way that:
    1. If a thrown HTTPException is an instance of PaymentException, then we handle it in our customized way
    2. If a thrown HTTPException is only an instance of HTTPException, then we just let
    default http_exception_handler handle it

    Note:
    1. This http exception handler shall be added at each sub-app level, since sub app's ExceptionMiddleWare will
    handler exceptions earlier than root app.
    2. Although PaymentException is a subclass of fastapi.HTTPException, when register this exception handler
    we should register it to handle starlette.exceptions.HTTPException.
    Why? see: https://fastapi.tiangolo.com/tutorial/handling-errors/#fastapis-httpexception-vs-starlettes-httpexception

    example:
    app = FastAPI()
    app.add_exception_handler(starlette.exceptions.HTTPException, payment_http_exception_handler)

    OR as a short cut, use:
    app.commons.error.errors.register_payment_exception_handler(app)

    See FastAPI error handling about re-use / override default http exception handler:
    https://fastapi.tiangolo.com/tutorial/handling-errors/#re-use-fastapis-exception-handlers

    :param request: starlette.Request
    :param exception: starlette.exceptions.HTTPException
    :return: Handled Http exception response
    """
    logger: BoundLogger = get_logger_from_req(request)
    logger.info(f"Translating source exception={str(exception)}")

    exception_response = None
    if isinstance(exception, PaymentException):
        exception_response = JSONResponse(
            status_code=exception.status_code,
            content=jsonable_encoder(
                PaymentErrorResponseBody(
                    error_code=exception.error_code,
                    error_message=exception.error_message,
                    retryable=exception.retryable,
                )
            ),
        )
    else:
        exception_response = await http_exception_handler(request, exception)

    return response_with_req_id(request, exception_response)


async def payment_internal_error_handler(
    request: Request, exception: Exception
) -> Response:
    logger: BoundLogger = get_logger_from_req(request)
    logger.exception(f"Translating source exception={exception}")

    return response_with_req_id(
        request,
        PlainTextResponse(
            "Internal Server Error", status_code=HTTP_500_INTERNAL_SERVER_ERROR
        ),
    )


async def payment_request_validation_exception_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    logger: BoundLogger = get_logger_from_req(request)
    logger.exception(f"Translating source exception={exception}")
    return response_with_req_id(
        request,
        JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exception.errors()},
        ),
    )


def register_payment_exception_handler(app: FastAPI):
    app.add_exception_handler(StarletteHTTPException, payment_http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, payment_request_validation_exception_handler
    )
    app.add_exception_handler(Exception, payment_internal_error_handler)
