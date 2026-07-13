from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException, DomainException

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers centralized exception handlers to translate pure domain exceptions
    into standardized HTTP JSON responses.
    """
    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": exc.message,
                "error_type": "EntityNotFound"
            }
        )

    @app.exception_handler(BusinessRuleViolationException)
    async def business_rule_violation_handler(request: Request, exc: BusinessRuleViolationException) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.message,
                "error_type": "BusinessRuleViolation"
            }
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": exc.message,
                "error_type": "InternalDomainError"
            }
        )
