"""
Zarinpal payment gateway integration (Request / Verify API).

Reference: https://docs.zarinpal.com/payment-gateway/

Flow:
    1. request_payment(amount, description, callback_url)
       -> POST /pg/v4/payment/request.json
       -> returns (authority, gateway_url)
    2. redirect the browser to gateway_url (Zarinpal hosted page)
    3. Zarinpal redirects back to callback_url?Status=OK&Authority=...
    4. verify_payment(authority, amount)
       -> POST /pg/v4/payment/verify.json
       -> returns (success, ref_id, message)
"""
import requests
from django.conf import settings


# --- Endpoints (sandbox vs production) -----------------------------
_REQUEST_URL = (
    "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    if settings.ZARINPAL_SANDBOX
    else "https://api.zarinpal.com/pg/v4/payment/request.json"
)
_VERIFY_URL = (
    "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    if settings.ZARINPAL_SANDBOX
    else "https://api.zarinpal.com/pg/v4/payment/verify.json"
)
_GATEWAY_BASE = (
    "https://sandbox.zarinpal.com/pg/StartPay/"
    if settings.ZARINPAL_SANDBOX
    else "https://www.zarinpal.com/pg/StartPay/"
)

_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class ZarinpalError(Exception):
    """Raised when Zarinpal returns a non-success response."""


def request_payment(amount: int, description: str, callback_url: str):
    """
    Step 1 — request a new payment from Zarinpal.

    :return: tuple (authority: str, gateway_url: str)
    :raises ZarinpalError: if the request fails or returns no authority.
    """
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": amount,
        "currency": "IRR",
        "description": description,
        "callback_url": callback_url,
    }
    response = requests.post(_REQUEST_URL, json=payload, headers=_HEADERS, timeout=15)
    data = response.json()

    authority = (data.get("data") or {}).get("authority")
    if not authority:
        errors = data.get("errors") or []
        msg = errors[0].get("message") if errors else "خطا در ارتباط با درگاه زرین‌پال"
        raise ZarinpalError(msg)

    return authority, f"{_GATEWAY_BASE}{authority}"


def verify_payment(authority: str, amount: int):
    """
    Step 2 — verify a payment after the user returns from Zarinpal.

    :return: tuple (success: bool, ref_id: str, message: str)
    """
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": amount,
        "authority": authority,
    }
    response = requests.post(_VERIFY_URL, json=payload, headers=_HEADERS, timeout=15)
    data = response.json()

    body = data.get("data") or {}
    code = body.get("code")
    # 100 = verified, 101 = already verified (still a success)
    if code in (100, 101):
        ref_id = str(body.get("ref_id") or "")
        return True, ref_id, "پرداخت با موفقیت تأیید شد."

    errors = data.get("errors") or []
    msg = errors[0].get("message") if errors else body.get("message") or "تأیید پرداخت ناموفق بود."
    return False, "", msg
