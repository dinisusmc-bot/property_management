"""
Seed notification templates for invoices, payments, and approvals
"""
import requests
import json

NOTIFICATION_SERVICE_URL = "http://localhost:8003"  # Adjust port when service is running

templates = [
    {
        "name": "invoice_notification",
        "notification_type": "email",
        "email_subject": "Invoice {{invoice_number}} from Athena Coach Services",
        "email_body_html": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Invoice {{invoice_number}}</h2>
                <p>Dear {{client_name}},</p>
                <p>Thank you for choosing Athena Coach Services. Please find your invoice details below:</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Invoice Number:</strong></td>
                            <td>{{invoice_number}}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Amount:</strong></td>
                            <td style="font-size: 18px; color: #2563eb;">{{total_amount}}</td>
                        </tr>
                        <tr>
                            <td><strong>Due Date:</strong></td>
                            <td>{{due_date}}</td>
                        </tr>
                    </table>
                </div>
                
                <p>Please remit payment by the due date to avoid any late fees.</p>
                <p>If you have any questions, please don't hesitate to contact us.</p>
                
                <p>Best regards,<br>
                Athena Coach Services Team</p>
            </div>
        </body>
        </html>
        """,
        "email_body_text": """
        Invoice {{invoice_number}}
        
        Dear {{client_name}},
        
        Thank you for choosing Athena Coach Services. Please find your invoice details below:
        
        Invoice Number: {{invoice_number}}
        Total Amount: {{total_amount}}
        Due Date: {{due_date}}
        
        Please remit payment by the due date to avoid any late fees.
        
        If you have any questions, please don't hesitate to contact us.
        
        Best regards,
        Athena Coach Services Team
        """,
        "description": "New invoice notification sent to clients"
    },
    {
        "name": "overdue_invoice_reminder",
        "notification_type": "email",
        "email_subject": "URGENT: Overdue Invoice {{invoice_number}} - {{days_overdue}} Days Past Due",
        "email_body_html": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #dc2626; margin: 0;">Payment Overdue</h2>
                </div>
                
                <p>Dear {{client_name}},</p>
                <p>This is a reminder that the following invoice is now <strong>{{days_overdue}} days past due</strong>:</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Invoice Number:</strong></td>
                            <td>{{invoice_number}}</td>
                        </tr>
                        <tr>
                            <td><strong>Balance Due:</strong></td>
                            <td style="font-size: 18px; color: #dc2626;">{{balance_due}}</td>
                        </tr>
                        <tr>
                            <td><strong>Original Due Date:</strong></td>
                            <td>{{due_date}}</td>
                        </tr>
                        <tr>
                            <td><strong>Days Overdue:</strong></td>
                            <td style="color: #dc2626;">{{days_overdue}} days</td>
                        </tr>
                    </table>
                </div>
                
                <p><strong>Please submit payment immediately to avoid service interruption and additional late fees.</strong></p>
                
                <p>If you have already sent payment, please disregard this notice. If you have questions about this invoice, please contact us immediately.</p>
                
                <p>Thank you for your prompt attention to this matter.</p>
                
                <p>Best regards,<br>
                Athena Coach Services Accounting</p>
            </div>
        </body>
        </html>
        """,
        "email_body_text": """
        PAYMENT OVERDUE
        
        Dear {{client_name}},
        
        This is a reminder that the following invoice is now {{days_overdue}} days past due:
        
        Invoice Number: {{invoice_number}}
        Balance Due: {{balance_due}}
        Original Due Date: {{due_date}}
        Days Overdue: {{days_overdue}} days
        
        Please submit payment immediately to avoid service interruption and additional late fees.
        
        If you have already sent payment, please disregard this notice.
        
        Thank you for your prompt attention to this matter.
        
        Best regards,
        Athena Coach Services Accounting
        """,
        "description": "Overdue payment reminder for past due invoices"
    },
    {
        "name": "upcoming_payment_reminder",
        "notification_type": "email",
        "email_subject": "Payment Reminder: {{payment_type}} Due {{due_date}}",
        "email_body_html": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Upcoming Payment Reminder</h2>
                <p>Dear {{client_name}},</p>
                <p>This is a friendly reminder that you have an upcoming payment due:</p>
                
                <div style="background-color: #dbeafe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Payment Type:</strong></td>
                            <td>{{payment_type}}</td>
                        </tr>
                        <tr>
                            <td><strong>Amount Due:</strong></td>
                            <td style="font-size: 18px; color: #2563eb;">{{amount_due}}</td>
                        </tr>
                        <tr>
                            <td><strong>Due Date:</strong></td>
                            <td>{{due_date}}</td>
                        </tr>
                        <tr>
                            <td><strong>Days Until Due:</strong></td>
                            <td>{{days_until_due}} days</td>
                        </tr>
                    </table>
                </div>
                
                <p>Please ensure payment is submitted by the due date.</p>
                <p>Thank you for your business!</p>
                
                <p>Best regards,<br>
                Athena Coach Services Team</p>
            </div>
        </body>
        </html>
        """,
        "email_body_text": """
        Upcoming Payment Reminder
        
        Dear {{client_name}},
        
        This is a friendly reminder that you have an upcoming payment due:
        
        Payment Type: {{payment_type}}
        Amount Due: {{amount_due}}
        Due Date: {{due_date}}
        Days Until Due: {{days_until_due}} days
        
        Please ensure payment is submitted by the due date.
        
        Thank you for your business!
        
        Best regards,
        Athena Coach Services Team
        """,
        "description": "Reminder for upcoming payments (3 days before due)"
    },
    {
        "name": "quote_approval_request",
        "notification_type": "email",
        "email_subject": "Action Required: Approve Quote for Charter on {{trip_date}}",
        "email_body_html": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Quote Approval Required</h2>
                <p>Dear {{client_name}},</p>
                <p>Please review and approve the following charter quote:</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Trip Date:</strong></td>
                            <td>{{trip_date}}</td>
                        </tr>
                        <tr>
                            <td><strong>Passengers:</strong></td>
                            <td>{{passengers}}</td>
                        </tr>
                        <tr>
                            <td><strong>Vehicle:</strong></td>
                            <td>{{vehicle_name}}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Cost:</strong></td>
                            <td style="font-size: 18px; color: #2563eb;">{{total_cost}}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{approval_link}}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Approve Quote
                    </a>
                </div>
                
                <p>This quote is valid until {{quote_expiry_date}}.</p>
                <p>If you have any questions or need modifications, please contact us.</p>
                
                <p>Best regards,<br>
                Athena Coach Services Team</p>
            </div>
        </body>
        </html>
        """,
        "email_body_text": """
        Quote Approval Required
        
        Dear {{client_name}},
        
        Please review and approve the following charter quote:
        
        Trip Date: {{trip_date}}
        Passengers: {{passengers}}
        Vehicle: {{vehicle_name}}
        Total Cost: {{total_cost}}
        
        To approve this quote, please visit: {{approval_link}}
        
        This quote is valid until {{quote_expiry_date}}.
        
        If you have any questions or need modifications, please contact us.
        
        Best regards,
        Athena Coach Services Team
        """,
        "description": "Request client approval/sign-off on quote"
    },
    {
        "name": "booking_confirmation",
        "notification_type": "email",
        "email_subject": "Booking Confirmed: Charter on {{trip_date}}",
        "email_body_html": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #10b981; margin: 0;">Booking Confirmed!</h2>
                </div>
                
                <p>Dear {{client_name}},</p>
                <p>Your charter has been confirmed. Below are your booking details:</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Confirmation Number:</strong></td>
                            <td>{{charter_id}}</td>
                        </tr>
                        <tr>
                            <td><strong>Trip Date:</strong></td>
                            <td>{{trip_date}}</td>
                        </tr>
                        <tr>
                            <td><strong>Passengers:</strong></td>
                            <td>{{passengers}}</td>
                        </tr>
                        <tr>
                            <td><strong>Vehicle:</strong></td>
                            <td>{{vehicle_name}}</td>
                        </tr>
                        <tr>
                            <td><strong>Pickup Location:</strong></td>
                            <td>{{pickup_location}}</td>
                        </tr>
                        <tr>
                            <td><strong>Pickup Time:</strong></td>
                            <td>{{pickup_time}}</td>
                        </tr>
                    </table>
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Deposit of {{deposit_amount}} is due within 48 hours</li>
                    <li>Balance of {{balance_amount}} is due 7 days before trip date</li>
                    <li>You will receive an invoice shortly</li>
                </ul>
                
                <p>We look forward to serving you!</p>
                
                <p>Best regards,<br>
                Athena Coach Services Team</p>
            </div>
        </body>
        </html>
        """,
        "email_body_text": """
        BOOKING CONFIRMED!
        
        Dear {{client_name}},
        
        Your charter has been confirmed. Below are your booking details:
        
        Confirmation Number: {{charter_id}}
        Trip Date: {{trip_date}}
        Passengers: {{passengers}}
        Vehicle: {{vehicle_name}}
        Pickup Location: {{pickup_location}}
        Pickup Time: {{pickup_time}}
        
        Next Steps:
        - Deposit of {{deposit_amount}} is due within 48 hours
        - Balance of {{balance_amount}} is due 7 days before trip date
        - You will receive an invoice shortly
        
        We look forward to serving you!
        
        Best regards,
        Athena Coach Services Team
        """,
        "description": "Confirmation email sent after booking is approved"
    }
]

def seed_templates():
    """Seed notification templates"""
    for template in templates:
        try:
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/templates",
                json=template,
                timeout=10
            )
            if response.status_code in [200, 201]:
                print(f"✓ Created template: {template['name']}")
            else:
                print(f"✗ Failed to create template {template['name']}: {response.text}")
        except Exception as e:
            print(f"✗ Error creating template {template['name']}: {e}")

if __name__ == "__main__":
    print("Seeding notification templates...")
    seed_templates()
    print("Done!")
