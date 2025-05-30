import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)  # Ensures logger name is 'reservations.sms_utils'


def send_sms_via_traccar(phone_number: str, message: str) -> bool:
    """
    Sends an SMS using the Traccar SMS Gateway with API Key authentication.

    Args:
        phone_number: The recipient's phone number in international format (e.g., +639...).
        message: The text message to send.

    Returns:
        True if the request was seemingly successful (e.g., 200 OK), False otherwise.
    """
    if not settings.TRACCAR_SMS_GATEWAY_URL:
        logger.error("TRACCAR_SMS_GATEWAY_URL is not configured in settings.")
        return False
    if not settings.TRACCAR_SMS_API_KEY:
        logger.error("TRACCAR_SMS_API_KEY is not configured in settings.")
        return False

    if not phone_number:
        logger.warning("Attempted to send SMS but no phone number was provided.")
        return False

    payload = {"to": phone_number, "message": message}

    headers = {
        "Content-Type": "application/json",
        "Authorization": settings.TRACCAR_SMS_API_KEY,
    }

    try:
        logger.debug(
            f"Attempting to send SMS to {phone_number} via {settings.TRACCAR_SMS_GATEWAY_URL}"
        )
        logger.debug(f"SMS Payload: {payload}")
        logger.debug(f"SMS Headers: {headers}")

        response = requests.post(
            settings.TRACCAR_SMS_GATEWAY_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()

        logger.info(
            f"SMS request to {phone_number} sent. Traccar Gateway response: {response.status_code} - {response.text[:200]}"
        )

        # Assuming 200 OK is the primary success indicator from Traccar Gateway for an accepted request.
        # The actual SMS delivery status is on the phone and in Traccar's logs.
        return response.status_code == 200

    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending SMS to {phone_number} via Traccar Gateway.")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Connection error sending SMS to {phone_number}. Is Traccar Gateway running and accessible at {settings.TRACCAR_SMS_GATEWAY_URL}?"
        )
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTP error sending SMS to {phone_number}: {e.response.status_code} - {e.response.text}"
        )
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred sending SMS to {phone_number}: {e}")
        return False
