import logging
from datetime import timedelta, timezone
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Payment, Booking

from .services.chapa_service import ChapaPaymentService

logger = logging.getLogger(__name__)


# pylint: disable=no-member
# pylint: disable=broad-exception-caught
# pylint: disable=unused-argument
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_email(self, booking_id):
    """
    Send booking confirmation email to user

    Args:
        booking_id: UUID string of the booking record

    Returns:
        Success message or error
    """
    try:
        # Fetch booking with related data
        booking = Booking.objects.select_related(
            "listing_id",
            "listing_id__host",
            "user",
        ).get(booking_id=booking_id)

        # Prepare email context
        context = {
            "user_name": booking.user.get_full_name(),
            "booking_reference": booking.booking_reference,
            "property_name": booking.listing_id.name,
            "property_location": booking.listing_id.location,
            "host_name": booking.listing_id.host.get_full_name(),
            "host_email": booking.listing_id.host.email,
            "host_phone": booking.listing_id.host.phone_number,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "total_nights": booking.total_nights,
            "total_price": booking.total_price,
            "price_per_night": booking.listing_id.pricepernight,
            "booking_status": booking.status,
            "created_at": booking.created_at,
        }

        # Render email templates
        subject = f"Booking Confirmation - {booking.booking_reference}"
        html_message = render_to_string("emails/booking_confirmation.html", context)
        plain_message = strip_tags(html_message)

        # Create email with both HTML and plain text
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        logger.info(
            "Booking confirmation email sent successfully for booking %s to %s",
            booking.booking_reference,
            booking.user.email,
        )

        return f"Email sent successfully to {booking.user.email}"

    except Booking.DoesNotExist:
        error_msg = f"Booking with id {booking_id} not found"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        logger.error("Error sending booking confirmation email: %s", e)
        # Retry the task with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for booking %s", booking_id)
            return f"Failed after {self.max_retries} retries: {str(e)}"


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_confirmation_email(self, payment_id):
    """
    Send payment confirmation email to user

    Args:
        payment_id: ID of the payment record

    Returns:
        Success message or error
    """
    try:
        payment = Payment.objects.select_related(
            "booking",
            "booking__listing_id",
            "booking__listing_id__host",
            "booking__user",
        ).get(payment_id=payment_id)

        # Prepare email context
        context = {
            "user_name": f"{payment.first_name} {payment.last_name}",
            "booking_reference": payment.booking.booking_reference,
            "property_name": payment.booking.listing_id.name,
            "property_location": payment.booking.listing_id.location,
            "host_name": payment.booking.listing_id.host.get_full_name(),
            "check_in": payment.booking.check_in,
            "check_out": payment.booking.check_out,
            "total_nights": payment.booking.total_nights,
            "amount": payment.amount,
            "currency": payment.currency,
            "transaction_id": payment.transaction_id,
            "payment_method": payment.payment_method or "N/A",
            "payment_date": payment.completed_at,
        }

        # Render email template
        subject = f"Payment Confirmation - Booking {payment.booking.booking_reference}"
        html_message = render_to_string("emails/payment_confirmation.html", context)
        plain_message = strip_tags(html_message)

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[payment.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        logger.info(
            "Payment confirmation email sent for payment %s", payment.transaction_id
        )
        return f"Email sent successfully to {payment.email}"

    except Payment.DoesNotExist:
        error_msg = f"Payment with id {payment_id} not found"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        logger.error("Error sending payment confirmation email: %s", e)
        try:
            raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for payment %s", payment_id)
            return f"Failed after {self.max_retries} retries: {str(e)}"


@shared_task(bind=True, max_retries=3)
def send_payment_failed_email(self, payment_id):
    """
    Send payment failure notification email

    Args:
        payment_id: UUID string of the payment record

    Returns:
        Success message or error
    """
    try:
        payment = Payment.objects.select_related(
            "booking",
            "booking__listing_id",
            "booking__listing_id__host",
            "booking__user",
        ).get(payment_id=payment_id)

        context = {
            "user_name": f"{payment.first_name} {payment.last_name}",
            "booking_reference": payment.booking.booking_reference,
            "property_name": payment.booking.listing_id.name,
            "property_location": payment.booking.listing_id.location,
            "check_in": payment.booking.check_in,
            "check_out": payment.booking.check_out,
            "amount": payment.amount,
            "currency": payment.currency,
            "transaction_id": payment.transaction_id,
            "retry_url": f"{settings.FRONTEND_URL}/bookings/{payment.booking.booking_id}/payment",
        }

        subject = f"Payment Failed - Booking {payment.booking.booking_reference}"
        html_message = render_to_string("emails/payment_failed.html", context)
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[payment.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        logger.info("Payment failed email sent for payment %s", payment.transaction_id)
        return f"Email sent successfully to {payment.email}"

    except Payment.DoesNotExist:
        error_msg = f"Payment with id {payment_id} not found"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        logger.error("Error sending payment confirmation email: %s", e)
        try:
            raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for payment %s", payment_id)
            return f"Failed after {self.max_retries} retries: {str(e)}"


@shared_task
def check_pending_payments():
    """
    Periodic task to check status of pending payments
    Run this task every hour using Celery Beat

    Returns:
        Summary of checked and updated payments
    """

    # Get payments pending for more than 1 hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    pending_payments = Payment.objects.filter(
        status="pending", created_at__lte=one_hour_ago
    )

    chapa_service = ChapaPaymentService()
    checked_count = 0
    updated_count = 0

    for payment in pending_payments:
        result = chapa_service.verify_payment(payment.transaction_id)
        checked_count += 1

        if result["success"]:
            data = result["data"]
            payment_status = data.get("status", "").lower()

            if payment_status != payment.status:
                payment.chapa_response = data
                payment.payment_method = data.get("payment_method", "")

                if payment_status == "success":
                    payment.mark_as_success()
                    send_payment_confirmation_email.delay(str(payment.payment_id))
                    updated_count += 1
                elif payment_status == "failed":
                    payment.mark_as_failed()
                    send_payment_failed_email.delay(str(payment.payment_id))
                    updated_count += 1

    summary = (
        f"Checked {checked_count} pending payments, updated {updated_count} statuses"
    )
    logger.info(summary)
    return summary


@shared_task(bind=True)
def send_booking_cancellation_email(self, booking_id):
    """
    Send booking cancellation email to user

    Args:
        booking_id: UUID string of the booking record
    """
    try:
        booking = Booking.objects.select_related("listing_id", "user").get(
            booking_id=booking_id
        )

        context = {
            "user_name": booking.user.get_full_name(),
            "booking_reference": booking.booking_reference,
            "property_name": booking.listing_id.name,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
        }

        subject = f"Booking Cancelled - {booking.booking_reference}"
        html_message = render_to_string("emails/booking_cancellation.html", context)
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        logger.info("Booking cancellation email sent for %s", booking.booking_reference)
        return f"Email sent successfully to {booking.user.email}"

    except Exception as e:
        logger.error("Error sending cancellation email: %s", e)
        return str(e)


@shared_task
def test_celery():
    """
    Simple test task to verify Celery is working
    """
    logger.info("Test task executed successfully!")
    return "Celery is working!"
