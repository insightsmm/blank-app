import stripe
import streamlit as st
from utils.db import update_payment


def get_stripe_client() -> bool:
    """
    Configure the stripe library with the company's secret key.
    Returns True if the key is set, False otherwise.
    """
    try:
        company = st.session_state.get("company", {}) or {}
        key = company.get("stripe_secret_key", "")
        if not key:
            return False
        stripe.api_key = key
        return True
    except Exception as e:
        print(f"get_stripe_client error: {e}")
        return False


def create_payment_link(
    amount_cents: int,
    description: str,
    client_email: str = None,
    metadata: dict = None,
) -> str | None:
    """
    Create a Stripe Payment Link and return the URL.
    amount_cents: integer amount in cents (e.g. 50000 = $500.00)
    """
    if not get_stripe_client():
        st.warning("Stripe is not configured. Add your Stripe secret key in Settings.")
        return None

    try:
        # Create a price object for one-time payment
        price = stripe.Price.create(
            unit_amount=amount_cents,
            currency="usd",
            product_data={"name": description},
        )

        # Build payment link params
        params = {
            "line_items": [{"price": price.id, "quantity": 1}],
            "metadata": metadata or {},
        }
        if client_email:
            params["customer_email"] = client_email

        link = stripe.PaymentLink.create(**params)
        return link.url

    except stripe.error.AuthenticationError:
        st.error("Stripe authentication failed. Check your secret key in Settings.")
        return None
    except Exception as e:
        print(f"create_payment_link error: {e}")
        st.error(f"Failed to create payment link: {str(e)}")
        return None


def create_invoice(
    client_email: str,
    client_name: str,
    items: list,
    due_days: int = 7,
) -> dict | None:
    """
    Create a Stripe Invoice with line items and return invoice details.

    items: list of dicts with keys: description, amount_cents (int), quantity (int, optional)
    Returns: {invoice_id, invoice_url, amount} or None
    """
    if not get_stripe_client():
        st.warning("Stripe is not configured. Add your Stripe secret key in Settings.")
        return None

    try:
        # Find or create customer
        existing = stripe.Customer.list(email=client_email, limit=1)
        if existing.data:
            customer = existing.data[0]
        else:
            customer = stripe.Customer.create(
                email=client_email,
                name=client_name,
            )

        # Create invoice
        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method="send_invoice",
            days_until_due=due_days,
            auto_advance=True,
        )

        # Add line items
        total_cents = 0
        for item in items:
            quantity = item.get("quantity", 1)
            amount_cents = int(item.get("amount_cents", 0))
            stripe.InvoiceItem.create(
                customer=customer.id,
                invoice=invoice.id,
                description=item.get("description", "Service"),
                unit_amount=amount_cents,
                quantity=quantity,
                currency="usd",
            )
            total_cents += amount_cents * quantity

        # Finalize and send
        finalized = stripe.Invoice.finalize_invoice(invoice.id)

        return {
            "invoice_id": finalized.id,
            "invoice_url": finalized.hosted_invoice_url or "",
            "amount": total_cents / 100,
        }

    except stripe.error.AuthenticationError:
        st.error("Stripe authentication failed. Check your secret key in Settings.")
        return None
    except Exception as e:
        print(f"create_invoice error: {e}")
        st.error(f"Failed to create invoice: {str(e)}")
        return None


def get_payment_status(payment_intent_id: str) -> str:
    """
    Retrieve the status of a Stripe PaymentIntent.
    Returns: 'succeeded' | 'pending' | 'failed' | 'canceled'
    """
    if not get_stripe_client():
        return "pending"

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        status = intent.status
        # Normalize to our expected values
        if status == "succeeded":
            return "succeeded"
        if status in ("canceled", "cancelled"):
            return "canceled"
        if status in ("requires_payment_method", "requires_confirmation", "requires_action"):
            return "pending"
        return status
    except Exception as e:
        print(f"get_payment_status error: {e}")
        return "pending"


def create_checkout_session(
    amount_cents: int,
    description: str,
    success_url: str,
    cancel_url: str,
    client_email: str = None,
) -> str | None:
    """
    Create a Stripe Checkout Session and return the session URL.
    Returns the checkout URL string, or None on failure.
    """
    if not get_stripe_client():
        st.warning("Stripe is not configured. Add your Stripe secret key in Settings.")
        return None

    try:
        params = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {"name": description},
                    },
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if client_email:
            params["customer_email"] = client_email

        session = stripe.checkout.Session.create(**params)
        return session.url

    except stripe.error.AuthenticationError:
        st.error("Stripe authentication failed. Check your secret key in Settings.")
        return None
    except Exception as e:
        print(f"create_checkout_session error: {e}")
        st.error(f"Failed to create checkout session: {str(e)}")
        return None


def format_amount_for_stripe(dollars) -> int:
    """Convert a dollar amount (float or str) to Stripe's integer cents format."""
    try:
        return int(round(float(dollars) * 100))
    except (TypeError, ValueError):
        return 0
