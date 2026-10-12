from src import config


class UserFacingError(Exception):
    """An error whose message is written for the user and can be shown as is."""


def friendly_message(exc: Exception) -> str:
    """Turns any exception into a plain-English message. Never includes a stack trace."""
    if isinstance(exc, UserFacingError):
        return str(exc)

    # Imported here, not at the top: importing inference takes 10 to 20 seconds, and this module is loaded
    # before the page is drawn. By the time a model error can happen, inference is already imported.
    import requests
    from inference.core.exceptions import (
        RoboflowAPIConnectionError,
        RoboflowAPINotAuthorizedError,
        RoboflowAPINotNotFoundError,
    )
    from inference_models.errors import (
        ForbiddenModelAccessError,
        ModelRetrievalError,
        PaymentRequiredModelAccessError,
        UnauthorizedModelAccessError,
        UsagePausedModelAccessError,
    )

    if isinstance(exc, (PaymentRequiredModelAccessError, UsagePausedModelAccessError)):
        return "Roboflow refused to serve the model because of the account's plan or usage limits. Check your Roboflow account."
    if isinstance(exc, (ForbiddenModelAccessError, UnauthorizedModelAccessError, RoboflowAPINotAuthorizedError)):
        return "Roboflow rejected the API key. Check ROBOFLOW_API_KEY in the .env file, then restart the app."
    if isinstance(exc, RoboflowAPINotNotFoundError):
        return (
            f"Roboflow could not find the model '{config.MODEL_ID}'. Check MODEL_ID in the .env file. "
            "It should look like project-name/version, for example planogram_sku110k/1."
        )
    # requests' ConnectionError and Timeout are not subclasses of the built-in ConnectionError.
    network_errors = (ConnectionError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    if isinstance(exc, (RoboflowAPIConnectionError, ModelRetrievalError, *network_errors)):
        return (
            "Could not reach Roboflow to download the model. Check your internet connection and try again. "
            "After the first successful download the model also works offline."
        )
    return "Something went wrong while processing the file. Check the terminal for details and try again."
