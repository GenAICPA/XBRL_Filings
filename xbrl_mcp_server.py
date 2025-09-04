from typing import Any, Dict, Optional
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "xbrl_filings",
    "XBRL Filings API",
    "A server to query the filings.xbrl.org database.",
)

# Constants for the XBRL Filings API
XBRL_API_BASE = "https://filings.xbrl.org/api"
USER_AGENT = "xbrl-mcp-server/1.0"

async def make_xbrl_request(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Makes a request to the filings.xbrl.org API with proper error handling.

    Args:
        params: A dictionary of query parameters for the request.

    Returns:
        The JSON response as a dictionary, or None if an error occurs.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.api+json"  # As per JSON:API spec
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{XBRL_API_BASE}/filings",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 4xx, 5xx)
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            # Handle other request errors (e.g., network issues)
            print(f"An error occurred while requesting {e.request.url!r}.")
            return None

@mcp.tool()
async def get_filings(
    country: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Get recent XBRL filings from the filings.xbrl.org database.

    Args:
        country: The two-letter ISO country code to filter filings by (e.g., US, GB).
        limit: The maximum number of filings to return. Defaults to 5.
    """
    api_params = {
        "page[size]": limit,
        "sort": "-processed",
        "include": "entity"  # Request to include the full entity object
    }
    if country:
        api_params["filter[country]"] = country.upper()

    response_data = await make_xbrl_request(api_params)

    if not response_data or not response_data.get("data"):
        return "Could not retrieve filings from the API."

    filings = response_data["data"]
    # Create a lookup map for included entities for efficient access
    included_entities = {
        item["id"]: item["attributes"] for item in response_data.get("included", [])
    }

    if not filings:
        return "No filings found matching your criteria."

    formatted_filings = []
    for filing in filings:
        attributes = filing.get("attributes", {})

        # Look up the entity name from the included data
        entity_relationship = filing.get("relationships", {}).get("entity", {}).get("data", {})
        entity_id = entity_relationship.get("id")
        entity_name = "Unknown Entity"
        if entity_id and entity_id in included_entities:
            entity_name = included_entities[entity_id].get("name", "Unknown Entity")

        report_url = attributes.get('report_url', 'No URL')
        # Format the date nicely
        processed_date = attributes.get('processed', 'No Date').split('T')[0]

        formatted_filings.append(
            f"Entity: {entity_name}\n"
            f"Processed Date: {processed_date}\n"
            f"Country: {attributes.get('country', 'N/A')}\n"
            f"Report URL: {report_url}"
        )

    return "\n---\n".join(formatted_filings)

if __name__ == "__main__":
    # This runs the MCP server, listening for messages over stdio.
    # It can be connected to an MCP client like Claude for Desktop.
    mcp.run(transport='stdio')
