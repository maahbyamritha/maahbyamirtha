# Shopify cart and checkout

Implemented in the current project:
- Available Shopify variant selection and quantity on product pages.
- Add to Cart; a cart page with quantity update and removal.
- Cart links in desktop navigation and mobile navigation/menus.
- Checkout POST fetches a fresh Shopify checkout URL and redirects there.
- Shopify controls line prices, totals and availability. No payment details are handled by Django.
- Guest cart ID stored in a signed, HttpOnly, SameSite cookie (Secure in production), not in a Django database session. Changes require CSRF-protected POST requests.
- Missing/expired carts recover to an empty cart; adding can create a new one. Network failures do not automatically retry cart mutations.
- Shopify inventory warnings are shown after redirect; cart pages are not cached.

Verification: automated cart/catalog tests, live Shopify create/update/remove checks, browser Add to Cart and Remove, desktop and mobile cart layouts, and successful navigation to the hosted Shopify checkout. Test carts were emptied. No payment or order was submitted.

Run the existing Django server from this folder, then open a product and choose Add to cart. Existing Shopify storefront credentials are used. On deployment run build.sh to regenerate collected static assets.

Shopify hosted customer login is now linked from /account/; see CUSTOMER-ACCOUNTS.md. Still separate work: removing the original Django admin/local category database dependencies, configuring Shopify payment/shipping settings, and testing a complete order with the merchant's chosen test-payment workflow. The existing production configuration still requires PostgreSQL until database dependencies are removed.

Private Storefront requests can include the validated direct buyer IP. Forwarded IP headers are intentionally not trusted by default; configure trusted proxy IP handling before customer account integration on a reverse-proxy host.
