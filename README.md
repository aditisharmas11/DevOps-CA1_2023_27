README entry (copy into README.md)
* Group (PRN -> name)
    * 23070122049: Arunabha Mukhopadhyay
    * 23070122033: Anshul Mandekar
    * 23070122060: Avi S Gupta
    * 23070122063: Ayaan Rukadikar
* Issue worked on
    * Title: Email 2FA fails on iOS app ("No password hash has been submitted") while working fine in browser
    * Link: https://github.com/dani-garcia/vaultwarden/issues/7568
* Pull request
    * Title: Allow email-only /api/two-factor/send-email-login for iOS mobile client (fix #7568)
    * Link: https://github.com/dani-garcia/vaultwarden/pull/7572
    * Branch: Arunabha-Mukhopadhyay:fix/email-2fa-ios-send-email-login
    * Commit: 4f26f725 — "Allow email-only /api/two-factor/send-email-login for mobile clients"
* Brief description of the change
    * Problem: The Bitwarden iOS client can call /api/two-factor/send-email-login with only the user's email; the server previously rejected such requests with "No password hash has been submitted", preventing the app from receiving the email 2FA code.
    * Fix: Permit email-only requests to /api/two-factor/send-email-login so the server generates and sends the email 2FA token for mobile clients. Rate-limiting is still applied.
    * File modified: src/api/core/two_factor/email.rs
* How to test locally
    1. Start the vaultwarden server with your usual local test environment.
    2. Trigger the mobile flow (or simulate with curl):
       curl -X POST http://localhost:8080/api/two-factor/send-email-login \
        -H "Content-Type: application/json" \
        -d '{"Email":"user@example.com"}'
    3. Verify server logs show the token was created/sent and that the user receives the email.
    4. Complete the login flow by submitting the token from the mobile client and verify login succeeds.
