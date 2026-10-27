import json
import urllib.request
import urllib.error

from django.conf import settings


SHOPIFY_API_VERSION = "2026-10"


def shopify_graphql(query, variables=None, buyer_ip=None):
    """
    Send a GraphQL request to the Shopify Storefront API.
    """

    url = (
        f"https://{settings.SHOPIFY_STORE_DOMAIN}"
        f"/api/{SHOPIFY_API_VERSION}/graphql.json"
    )

    payload = json.dumps({
        "query": query,
        "variables": variables or {},
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Use the private Storefront token if one is configured.
    token = getattr(
        settings,
        "SHOPIFY_STOREFRONT_PRIVATE_TOKEN",
        None,
    )

    if token:
        headers["Shopify-Storefront-Private-Token"] = token.strip()

    if buyer_ip:
        headers["Shopify-Storefront-Buyer-IP"] = buyer_ip

    request = urllib.request.Request(
        url=url,
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except urllib.error.HTTPError as error:
        error.read()

        print("\n--- SHOPIFY ERROR ---")
        print("HTTP status:", error.code)
        # Do not log responses that might contain cart or customer identifiers.
        print("---------------------\n")

        raise

    except urllib.error.URLError as error:
        print("\n--- CONNECTION ERROR ---")
        print("Could not connect to Shopify.")
        print("Reason:", error.reason)
        print("------------------------\n")

        raise


def get_shopify_products(first=5):
    """
    Fetch products from Shopify.
    """

    query = """
    query GetProducts($first: Int!) {
        products(first: $first) {
            nodes {
                id
                title
                handle
                description
                availableForSale

                featuredImage {
                    url
                    altText
                }

                priceRange {
                    minVariantPrice {
                        amount
                        currencyCode
                    }
                }

                variants(first: 10) {
                    nodes {
                        id
                        title
                        availableForSale

                        price {
                            amount
                            currencyCode
                        }
                    }
                }
            }
        }
    }
    """

    result = shopify_graphql(
        query,
        {
            "first": first,
        },
    )

    # GraphQL can return HTTP 200 while still containing errors.
    if result.get("errors"):
        print("\n--- SHOPIFY GRAPHQL ERROR ---")
        print(json.dumps(result["errors"], indent=2))
        print("-----------------------------\n")

    return result