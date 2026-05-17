import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st
from utils.db import log_email
import base64
from datetime import datetime


def get_gmail_credentials():
    """Return (gmail_email, app_password) from company settings, or (None, None)."""
    try:
        company = st.session_state.get("company", {}) or {}
        gmail_email = company.get("gmail_email", "")
        app_password = company.get("gmail_app_password", "")
        if gmail_email and app_password:
            return gmail_email, app_password
        return None, None
    except Exception as e:
        print(f"get_gmail_credentials error: {e}")
        return None, None


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    attachments: list = None,
    cc: list = None,
) -> bool:
    """
    Send an HTML email via Gmail SMTP.

    attachments: list of (filename, bytes) tuples
    cc: list of email addresses
    """
    gmail_email, app_password = get_gmail_credentials()
    if not gmail_email or not app_password:
        st.warning(
            "Gmail credentials are not configured. Go to Settings to add your Gmail email and App Password."
        )
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = gmail_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)

        # HTML body
        html_part = MIMEText(body_html, "html")
        msg.attach(html_part)

        # Optional attachments
        if attachments:
            for filename, file_bytes in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}",
                )
                msg.attach(part)

        # Send via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_email, app_password)
            recipients = [to_email] + (cc or [])
            server.sendmail(gmail_email, recipients, msg.as_string())

        # Log the email
        company = st.session_state.get("company", {}) or {}
        log_email(
            {
                "company_id": company.get("id"),
                "from_email": gmail_email,
                "to_email": to_email,
                "subject": subject,
                "body": body_html[:2000],
                "status": "sent",
            }
        )
        return True

    except smtplib.SMTPAuthenticationError:
        st.error(
            "Gmail authentication failed. Check your Gmail email and App Password in Settings."
        )
        company = st.session_state.get("company", {}) or {}
        log_email(
            {
                "company_id": company.get("id"),
                "from_email": gmail_email,
                "to_email": to_email,
                "subject": subject,
                "body": body_html[:2000],
                "status": "failed",
                "error_message": "SMTP Authentication Error",
            }
        )
        return False
    except Exception as e:
        print(f"send_email error: {e}")
        company = st.session_state.get("company", {}) or {}
        log_email(
            {
                "company_id": company.get("id"),
                "from_email": gmail_email,
                "to_email": to_email,
                "subject": subject,
                "body": body_html[:2000],
                "status": "failed",
                "error_message": str(e)[:500],
            }
        )
        return False


def send_proposal_email(
    client_email: str,
    client_name: str,
    estimate: dict,
    pdf_bytes: bytes,
) -> bool:
    """Send a professionally formatted proposal email with a PDF attachment."""
    company = st.session_state.get("company", {}) or {}
    company_name = company.get("name", "ServicePro")
    company_phone = company.get("phone", "")
    company_email = company.get("email", "")

    trade_type = (estimate.get("trade_type") or "Service").title()
    total = float(estimate.get("total", 0) or 0)

    subject = f"Your Service Proposal from {company_name}"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; color: #1F2937; margin: 0; padding: 0; background: #F9FAFB; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #10B981, #3B82F6); padding: 2rem; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 1.8rem; }}
            .header p {{ color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; }}
            .content {{ padding: 2rem; }}
            .highlight-box {{ background: #F0FDF4; border-left: 4px solid #10B981; padding: 1rem; border-radius: 4px; margin: 1rem 0; }}
            .cta-button {{ display: inline-block; background: #10B981; color: white; padding: 0.75rem 2rem; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 1rem 0; }}
            .footer {{ background: #F9FAFB; padding: 1.5rem; text-align: center; color: #6B7280; font-size: 0.85rem; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 {company_name}</h1>
                <p>Professional {trade_type} Services</p>
            </div>
            <div class="content">
                <p>Dear {client_name},</p>
                <p>Thank you for considering {company_name} for your upcoming project. We're pleased to present your personalized proposal.</p>

                <div class="highlight-box">
                    <strong>Proposal Summary</strong><br>
                    Service Type: {trade_type}<br>
                    Estimated Total: <strong>${total:,.2f}</strong>
                </div>

                <p>Please review the attached PDF proposal for the complete breakdown of services, pricing, and terms. The proposal includes:</p>
                <ul>
                    <li>Detailed scope of work</li>
                    <li>Itemized pricing</li>
                    <li>Project timeline</li>
                    <li>Terms and conditions</li>
                </ul>

                <p>If you have any questions or would like to discuss the proposal, please don't hesitate to contact us:</p>
                <ul>
                    {"<li>📞 " + company_phone + "</li>" if company_phone else ""}
                    {"<li>📧 " + company_email + "</li>" if company_email else ""}
                </ul>

                <p>We look forward to working with you!</p>
                <p>Best regards,<br><strong>{company_name} Team</strong></p>
            </div>
            <div class="footer">
                <p>{company_name} | Professional Field Services</p>
                <p style="font-size:0.75rem; color:#9CA3AF;">This email was sent to {client_email}. If you received this in error, please disregard.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=client_email,
        subject=subject,
        body_html=body_html,
        attachments=[("proposal.pdf", pdf_bytes)],
    )


def send_appointment_reminder(
    client_email: str,
    client_name: str,
    job_title: str,
    date: str,
    time: str,
    address: str,
) -> bool:
    """Send a clean appointment reminder email to a client."""
    company = st.session_state.get("company", {}) or {}
    company_name = company.get("name", "ServicePro")
    company_phone = company.get("phone", "")

    subject = f"Appointment Reminder: {job_title}"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; color: #1F2937; margin: 0; padding: 0; background: #F9FAFB; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #10B981, #3B82F6); padding: 1.5rem 2rem; }}
            .header h1 {{ color: white; margin: 0; font-size: 1.4rem; }}
            .content {{ padding: 2rem; }}
            .detail-row {{ display: flex; margin: 0.75rem 0; }}
            .detail-label {{ font-weight: 600; min-width: 80px; color: #6B7280; }}
            .reminder-box {{ background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; border-radius: 4px; margin: 1rem 0; }}
            .footer {{ background: #F9FAFB; padding: 1.5rem; text-align: center; color: #6B7280; font-size: 0.85rem; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Appointment Reminder</h1>
            </div>
            <div class="content">
                <p>Dear {client_name},</p>
                <p>This is a friendly reminder about your upcoming appointment with <strong>{company_name}</strong>.</p>

                <div class="reminder-box">
                    <strong>⏰ Appointment Details</strong><br><br>
                    <strong>Service:</strong> {job_title}<br>
                    <strong>Date:</strong> {date}<br>
                    <strong>Time:</strong> {time}<br>
                    <strong>Location:</strong> {address}
                </div>

                <p>Please ensure access to the work area at the scheduled time. If you need to reschedule or have any questions, please contact us as soon as possible.</p>

                {"<p>📞 " + company_phone + "</p>" if company_phone else ""}

                <p>Thank you for choosing {company_name}. We look forward to seeing you!</p>
                <p>Best regards,<br><strong>{company_name} Team</strong></p>
            </div>
            <div class="footer">
                <p>{company_name} | Professional Field Services</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=client_email,
        subject=subject,
        body_html=body_html,
    )


def get_recent_emails(limit: int = 20) -> list:
    """
    Fetch recent emails from Gmail IMAP inbox.
    Returns a list of dicts: {from, to, subject, date, body_preview, message_id}
    """
    gmail_email, app_password = get_gmail_credentials()
    if not gmail_email or not app_password:
        return []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_email, app_password)
        mail.select("INBOX")

        # Search for recent messages
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return []

        message_ids = messages[0].split()
        # Take the most recent `limit` messages
        recent_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        recent_ids = list(reversed(recent_ids))  # newest first

        emails = []
        for msg_id in recent_ids:
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract body preview
                body_preview = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body_preview = part.get_payload(decode=True).decode(
                                    "utf-8", errors="replace"
                                )[:200]
                            except Exception:
                                body_preview = ""
                            break
                else:
                    try:
                        body_preview = msg.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )[:200]
                    except Exception:
                        body_preview = ""

                emails.append(
                    {
                        "from": msg.get("From", ""),
                        "to": msg.get("To", ""),
                        "subject": msg.get("Subject", "(No Subject)"),
                        "date": msg.get("Date", ""),
                        "body_preview": body_preview.strip(),
                        "message_id": msg.get("Message-ID", str(msg_id)),
                    }
                )
            except Exception as inner_e:
                print(f"Error parsing email {msg_id}: {inner_e}")
                continue

        mail.logout()
        return emails

    except imaplib.IMAP4.error as e:
        print(f"IMAP error in get_recent_emails: {e}")
        return []
    except Exception as e:
        print(f"get_recent_emails error: {e}")
        return []


def send_invoice_email(
    client_email: str,
    client_name: str,
    job_title: str,
    amount: float,
    payment_link: str,
) -> bool:
    """Send an invoice email to a client with a payment link."""
    company = st.session_state.get("company", {}) or {}
    company_name = company.get("name", "ServicePro")
    company_phone = company.get("phone", "")

    subject = f"Invoice from {company_name} — {job_title}"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; color: #1F2937; margin: 0; padding: 0; background: #F9FAFB; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #10B981, #3B82F6); padding: 1.5rem 2rem; }}
            .header h1 {{ color: white; margin: 0; font-size: 1.4rem; }}
            .content {{ padding: 2rem; }}
            .amount-box {{ background: #F0FDF4; border: 2px solid #10B981; border-radius: 12px; padding: 1.5rem; text-align: center; margin: 1.5rem 0; }}
            .amount {{ font-size: 2.5rem; font-weight: 800; color: #065F46; }}
            .pay-button {{ display: block; background: #10B981; color: white !important; padding: 1rem 2rem; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 1.1rem; text-align: center; margin: 1.5rem 0; }}
            .footer {{ background: #F9FAFB; padding: 1.5rem; text-align: center; color: #6B7280; font-size: 0.85rem; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧾 Invoice from {company_name}</h1>
            </div>
            <div class="content">
                <p>Dear {client_name},</p>
                <p>Thank you for choosing {company_name}. Your invoice for <strong>{job_title}</strong> is ready.</p>

                <div class="amount-box">
                    <div style="color:#6B7280; font-size:0.9rem; margin-bottom:0.5rem;">Amount Due</div>
                    <div class="amount">${amount:,.2f}</div>
                </div>

                <a href="{payment_link}" class="pay-button">💳 Pay Now Securely</a>

                <p style="font-size:0.85rem; color:#6B7280;">
                    You can also copy and paste this link into your browser:<br>
                    <a href="{payment_link}">{payment_link}</a>
                </p>

                <p>Payment is processed securely through Stripe. If you have any questions about this invoice, please contact us:</p>
                {"<p>📞 " + company_phone + "</p>" if company_phone else ""}

                <p>Thank you for your business!</p>
                <p>Best regards,<br><strong>{company_name} Team</strong></p>
            </div>
            <div class="footer">
                <p>{company_name} | Professional Field Services</p>
                <p style="font-size:0.75rem; color:#9CA3AF;">Payments are processed securely via Stripe.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=client_email,
        subject=subject,
        body_html=body_html,
    )
