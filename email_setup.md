# Gmail App Password Setup

To send email alerts, you need a Gmail App Password (regular passwords won't work with SMTP).

## Steps

1. **Enable 2-Step Verification** on your Google account:
   - Go to https://myaccount.google.com/security
   - Under "How you sign in to Google", click **2-Step Verification**
   - Follow the prompts to enable it

2. **Generate an App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select app: **Mail**
   - Click **Generate**
   - Copy the 16-character password (spaces don't matter)

3. **Configure `email_credentials/credentials.json`:**
   ```json
   {
       "gmail_user": "your.email@gmail.com",
       "gmail_app_password": "abcd efgh ijkl mnop",
       "alert_to": "recipient@gmail.com"
   }
   ```

## Troubleshooting

- If "App passwords" doesn't appear, make sure 2-Step Verification is enabled first.
- If you get "Authentication failed", double-check the app password (not your regular password).
- Google Workspace accounts may need admin approval for App Passwords.
