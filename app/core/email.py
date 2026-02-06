"""Email service for sending notifications.

Reads SMTP configuration from application settings (environment variables) so
credentials are not hard-coded in source.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with templates.

    Uses `settings` for SMTP configuration. If required SMTP settings are
    missing the service will log an error and return False when attempting to
    send.
    """

    def __init__(self):
        # Use settings (reads .env via pydantic BaseSettings)
        self.smtp_host = settings.SMTP_SERVER or "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        # FROM email/name: prefer explicit FROM env var, fall back to SMTP username
        self.from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        self.from_name = settings.SMTP_FROM_NAME or "RiskTrix TPRM System"

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email with HTML content
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text alternative (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Validate SMTP credentials
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials are not configured. Set SMTP_USERNAME and SMTP_PASSWORD in environment.")
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            
            # Add plain text version if provided
            if plain_content:
                part1 = MIMEText(plain_content, 'plain')
                message.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, 'html')
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_vendor_expiry_notification(
        self,
        vendor_name: str,
        vendor_category: str,
        expiry_date: date,
        to_email: str,
        days_until_expiry: int,
        vendor_id: Optional[int] = None
    ) -> bool:
        """
        Send vendor certificate expiry notification email
        
        Args:
            vendor_name: Name of the vendor
            vendor_category: Category of the vendor
            expiry_date: Certificate expiry date
            to_email: Vendor contact email
            days_until_expiry: Number of days until expiry
            vendor_id: Vendor ID (optional)
        
        Returns:
            bool: True if email sent successfully
        """
        # Format expiry date
        expiry_str = expiry_date.strftime("%B %d, %Y")
        
        # Determine urgency level
        if days_until_expiry <= 0:
            urgency = "EXPIRED"
            urgency_color = "#dc2626"
            status_message = "⚠️ EXPIRED"
        elif days_until_expiry <= 3:
            urgency = "CRITICAL"
            urgency_color = "#dc2626"
            status_message = f"⚠️ Expires in {days_until_expiry} days"
        elif days_until_expiry <= 8:
            urgency = "URGENT"
            urgency_color = "#ea580c"
            status_message = f"⚡ Expires in {days_until_expiry} days"
        else:
            urgency = "WARNING"
            urgency_color = "#f59e0b"
            status_message = f"⏰ Expires in {days_until_expiry} days"
        
        # Create HTML email
        html_content = self._create_expiry_email_template(
            vendor_name=vendor_name,
            vendor_category=vendor_category,
            expiry_date=expiry_str,
            days_until_expiry=days_until_expiry,
            urgency=urgency,
            urgency_color=urgency_color,
            status_message=status_message,
            vendor_id=vendor_id
        )
        
        # Create plain text version
        plain_content = f"""
RiskTrix TPRM System - Vendor Certificate Expiry Notification

Dear {vendor_name} Team,

This is an automated notification regarding your vendor certificate status.

Vendor Details:
- Name: {vendor_name}
- Category: {vendor_category}
- Certificate Expiry Date: {expiry_str}
- Status: {status_message}

ACTION REQUIRED:
Please update your vendor certificate to maintain compliance and continue your services.

If you have already renewed your certificate, please contact us with the updated information.

Thank you,
RiskTrix TPRM Team
        """
        
        # Send email
        subject = f"🔔 [{urgency}] Vendor Certificate Expiry Notice - {vendor_name}"

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content,
        )
    
    def _create_expiry_email_template(
        self,
        vendor_name: str,
        vendor_category: str,
        expiry_date: str,
        days_until_expiry: int,
        urgency: str,
        urgency_color: str,
        status_message: str,
        vendor_id: Optional[int] = None
    ) -> str:
        """Create HTML email template for vendor expiry notification"""
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vendor Certificate Expiry Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 40px 0;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
                    
                    <!-- Header with Logo/Brand -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #3949ab 0%, #1e88e5 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">
                                🛡️ RiskTrix TPRM System
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e3f2fd; font-size: 14px; opacity: 0.9;">
                                Third Party Risk Management
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Alert Badge -->
                    <tr>
                        <td style="padding: 30px 30px 20px 30px; text-align: center;">
                            <div style="display: inline-block; background-color: {urgency_color}; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                {urgency} NOTIFICATION
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 22px; font-weight: 600;">
                                Vendor Certificate Expiry Notice
                            </h2>
                            
                            <p style="margin: 0 0 25px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                Dear <strong>{vendor_name}</strong> Team,
                            </p>
                            
                            <p style="margin: 0 0 25px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                This is an automated notification regarding your vendor certificate status in our Third Party Risk Management system.
                            </p>
                            
                            <!-- Vendor Details Card -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f9fafb; border-radius: 8px; margin: 25px 0; border: 2px solid #e5e7eb;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500; width: 45%;">
                                                    Vendor Name:
                                                </td>
                                                <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">
                                                    {vendor_name}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500; border-top: 1px solid #e5e7eb;">
                                                    Category:
                                                </td>
                                                <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600; border-top: 1px solid #e5e7eb;">
                                                    {vendor_category}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500; border-top: 1px solid #e5e7eb;">
                                                    Certificate Expiry Date:
                                                </td>
                                                <td style="padding: 8px 0; color: {urgency_color}; font-size: 14px; font-weight: 700; border-top: 1px solid #e5e7eb;">
                                                    {expiry_date}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500; border-top: 1px solid #e5e7eb;">
                                                    Status:
                                                </td>
                                                <td style="padding: 8px 0; color: {urgency_color}; font-size: 14px; font-weight: 700; border-top: 1px solid #e5e7eb;">
                                                    {status_message}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Action Required Section -->
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin: 25px 0;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; font-weight: 600;">
                                    ⚠️ ACTION REQUIRED
                                </p>
                                <p style="margin: 10px 0 0 0; color: #92400e; font-size: 13px; line-height: 1.5;">
                                    Please update your vendor certificate to maintain compliance and continue providing services. Failure to update may result in service interruption.
                                </p>
                            </div>
                            
                            <!-- Next Steps -->
                            <div style="margin: 25px 0;">
                                <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                    📋 Next Steps:
                                </h3>
                                <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.8;">
                                    <li>Renew your vendor certificate immediately</li>
                                    <li>Submit updated certificate documentation to our compliance team</li>
                                    <li>Contact us if you need assistance or have already renewed</li>
                                </ul>
                            </div>
                            
                            <!-- Call to Action Button -->
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="mailto:educationforyou2025@gmail.com" style="display: inline-block; background: linear-gradient(135deg, #3949ab 0%, #1e88e5 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(57, 73, 171, 0.3);">
                                    📧 Contact Compliance Team
                                </a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px;">
                                This is an automated notification from RiskTrix TPRM System
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                © 2026 RiskTrix. All rights reserved.
                            </p>
                            {f'<p style="margin: 10px 0 0 0; color: #9ca3af; font-size: 11px;">Vendor ID: {vendor_id}</p>' if vendor_id else ''}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """


# Create singleton instance
email_service = EmailService()
