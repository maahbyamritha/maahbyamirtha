# Shopify customer sign-in

Open /account/ (or /login/) or use the account icon beside the burger menu.
The MAAH page links to /account/login/, which redirects to the configured store's /account URL. Shopify handles email verification, account creation, sign-out, profile details and order history on its hosted pages.

The live store's account route was verified to reach Shopify's branded email sign-in screen. No email, verification code or customer details were submitted during testing.

This is hosted customer accounts, not a Customer Account API integration. Django does not create an authenticated customer session, display customer names, or associate the guest cart with an account access token. Customers manage their account on Shopify. Guest checkout continues to work, with Shopify offering sign-in at checkout.

Optional: set SHOPIFY_CUSTOMER_ACCOUNT_URL to a trusted HTTPS customer account URL if you configure a branded accounts domain. Otherwise the existing SHOPIFY_STORE_DOMAIN is used automatically. Do not copy temporary OAuth URLs or verification URLs into configuration.

For customer email verification, ensure Shopify Settings > Customer accounts uses customer accounts. Account branding and policies are managed in Shopify.

Verification: 28 Django tests passed; desktop and mobile login layouts inspected; Continue to sign in reached the store's Shopify email form. A customer should test receiving and entering their own code to verify the final account experience.

The project's original Django admin and local category dependencies still need to be removed before deploying without PostgreSQL.
