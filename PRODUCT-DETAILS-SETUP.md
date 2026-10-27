# Product page setup in Shopify

Create three product metafield definitions under Shopify Settings > Metafields and metaobjects (or Custom data) > Products:

| Name | Namespace and key | Type |
| --- | --- | --- |
| Fabric | custom.fabric | Single line text |
| Length | custom.length | Single line text |
| Care | custom.care | Multi-line text |

Enable Storefront API access for each definition. Open each product and fill in its actual values. Blank or unavailable fields are hidden rather than replaced with sample facts.

Add the product tag `new` to show the New badge. Remove it when no longer appropriate.
Assign products to their published Shopify collection, such as Silk. If a product belongs to several collections, the site prefers a collection matching Product type, then a non-generic collection, then alphabetical title order (among the first 20 returned). The label and Back link point to that collection. Without a collection, Product type is the label if available; Back to sarees opens New Arrivals.

The page uses Shopify title, description, image and price. It keeps a Sold out notice for unavailable products. It removes the breadcrumb and the Available line to match the old layout.

Verification: seven automated Django tests passed using mocked Shopify responses. Live store metafield values and browser appearance have not been verified.
