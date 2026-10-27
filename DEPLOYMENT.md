# MAAH deployment

This is a Django storefront backed by Shopify. Use a Python 3.14 web service and persistent PostgreSQL database. Product images remain on Shopify; this deployment does not provide persistent storage for Django admin file uploads. Manage the catalog in Shopify.

## Render configuration

- Build: `bash build.sh`
- Start: `bash start.sh`
- Health check: `/health/`
- Environment: configure the names in `.env.production.example` in Render's environment settings.
- Render supplies `RENDER_EXTERNAL_HOSTNAME`; additional domains go in `DJANGO_ALLOWED_HOSTS` as a comma-separated list.
- Generate a fresh production Django secret key on the host. Keep the Shopify private token in the host's secret environment, never in source control.
- Set `DATABASE_URL` to the persistent PostgreSQL connection string.
- Select and approve hosting/database prices before creating paid resources.

Deployment runs database migrations and collects versioned static assets. The local SQLite database, local .env, admin credentials, and media uploads must not be uploaded. Seed migrations create the editorial collection placeholders. Publish matching Shopify collections to Headless to populate them.

## Verification before sharing

Check `/health/`, homepage, `/new-arrivals/`, `/product/test-saree/`, and the product image. Confirm HTTPS redirects, production debug mode off, and no private token in HTML. Verify contact details and product information before inviting customers. Checkout is not implemented; the site currently supports browsing and enquiries.

The project has not been deployed until a public URL is created and these checks pass.

Email delivery requires SMTP configuration before enabling email-based features.
