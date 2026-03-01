"""Email notification for price drops via Gmail SMTP."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_price_drop_email(
    product_name: str,
    old_price: float,
    new_price: float,
    url: str,
) -> None:
    """Send an email alert about a price drop.

    Reads credentials from environment variables:
        SENDER_EMAIL, SENDER_APP_PASSWORD, RECIPIENT_EMAIL
    """
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([sender, password, recipient]):
        logger.warning(
            "Email credentials not configured — skipping notification. "
            "Set SENDER_EMAIL, SENDER_APP_PASSWORD, and RECIPIENT_EMAIL."
        )
        return

    discount_pct = ((old_price - new_price) / old_price) * 100

    subject = f"Price Drop: {product_name} is now ${new_price:.2f}!"

    body_text = (
        f"{product_name}\n\n"
        f"Old price: ${old_price:.2f}\n"
        f"New price: ${new_price:.2f}\n"
        f"Discount:  {discount_pct:.1f}% off\n\n"
        f"Buy it here: {url}\n"
    )

    body_html = f"""\
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
  <h2 style="color: #333;">Price Drop Alert</h2>
  <h3>{product_name}</h3>
  <p>
    <span style="text-decoration: line-through; color: #999;">${old_price:.2f}</span>
    &nbsp;&rarr;&nbsp;
    <span style="color: #c0392b; font-size: 1.3em; font-weight: bold;">${new_price:.2f}</span>
  </p>
  <p style="color: #27ae60; font-weight: bold;">{discount_pct:.1f}% off</p>
  <p><a href="{url}" style="color: #2980b9;">View on Aritzia</a></p>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logger.info("Sent price drop email for %s to %s", product_name, recipient)
    except smtplib.SMTPException:
        logger.exception("Failed to send email for %s", product_name)
