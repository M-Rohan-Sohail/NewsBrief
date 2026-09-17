import logging
from exponent_server_sdk import (
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError

logger = logging.getLogger(__name__)

def send_push_message(token, title, message, extra=None):
    try:
        response = PushClient().publish(
            PushMessage(
                to=token,
                title=title,
                body=message,
                data=extra,
                sound="default"
            )
        )
        return response
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        logger.error(
            f"PushServerError: {exc.errors} - {exc.response_data}"
        )
        raise
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in production
        logger.error(
            f"Connection/HTTP Error sending push: {exc}"
        )
        raise
    except Exception as exc:
        logger.error(f"Unexpected error sending push: {exc}")
        raise
