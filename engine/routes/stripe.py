"""Stripe webhook routes — migrated from Flask (Phase 3)."""

from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["stripe"])


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request) -> Response:
    """
    Stripe webhook endpoint. Verifies signature and processes checkout.session.completed.
    Public path — no FORGE API key required.
    """
    from platform.stripe_handler import process_stripe_webhook

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    status_code, body = process_stripe_webhook(payload, sig_header)
    return Response(content=body, status_code=status_code, media_type="text/plain")