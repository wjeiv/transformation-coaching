# Email Configuration Setup

To enable email sending for the contact form, you need to configure SMTP settings.

## Gmail Setup (Recommended)

1. **Enable App Passwords:**
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification
   - Enable 2-Step Verification if not already enabled
   - Go to App passwords
   - Generate a new app password for "Mail" on "Other (custom name)"
   - Use this app password (not your regular password)

2. **Configure Environment Variables:**
   ```bash
   # In backend/dev.env or your environment
   SMTP_USERNAME=your-gmail-address@gmail.com
   SMTP_PASSWORD=your-16-character-app-password
   ```

## Alternative SMTP Providers

You can use any SMTP provider by updating these settings:
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP server port (usually 587 for TLS)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password

## Email Destination

Contact form submissions are sent to: `transformation.coaching26.2@gmail.com`

## Testing

After configuration, restart the backend service and test the contact form. The system will:
1. Save the submission to the database
2. Send an email notification with the submission details
3. Return success status to the frontend

## Troubleshooting

- **Email not sending**: Check SMTP credentials and ensure app passwords are enabled
- **Authentication failed**: Verify username and app password are correct
- **Connection refused**: Check SMTP host and port settings
