#!/usr/bin/env python3

# Immediately redirect stdout to prevent any contamination
import sys
import os

# Save the original stdout for MCP protocol
_original_stdout = sys.stdout

# Create a temporary buffer for any stray output
class StartupBuffer:
    def __init__(self):
        self.buffer = []
        self.stderr = sys.stderr
    
    def write(self, text):
        # During startup, log any stdout attempts to stderr
        if text.strip():
            self.stderr.write(f"[STARTUP] Blocking stdout: {repr(text)}\n")
            self.stderr.flush()
    
    def flush(self):
        pass

# Redirect stdout during imports and setup
sys.stdout = StartupBuffer()

try:
    # Now import everything
    from typing import Any, Dict, Optional, List
    import logging
    import httpx
    from mcp.server.fastmcp import FastMCP

    # Configure logging to stderr only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stderr,
        force=True
    )
    logger = logging.getLogger(__name__)

    # Initialize FastMCP server
    mcp = FastMCP(
        name="xbrl_filings",
        instructions="A server to query the filings.xbrl.org database.",
    )

    # Constants
    XBRL_API_BASE = "https://filings.xbrl.org/api"
    USER_AGENT = "xbrl-mcp-server/1.0"

    async def make_xbrl_request(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Makes a request to the filings.xbrl.org API."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.api+json"
        }
        
        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Making request to: {url}")
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    @mcp.tool()
    async def get_filings(
        country: Optional[str] = None,
        page_size: int = 5,
        page_number: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get recent XBRL filings from the filings.xbrl.org database.

        Args:
            country: The two-letter ISO country code to filter filings by (e.g., US, GB).
            page_size: The number of filings to return per page. Defaults to 5.
            page_number: The page number to retrieve. Defaults to 1.
        """
        try:
            logger.info(f"get_filings: country={country}, page_size={page_size}, page_number={page_number}")
            
            api_params = {
                "page[size]": str(page_size),
                "page[number]": str(page_number),
                "sort": "-processed",
                "include": "entity"
            }
            
            if country:
                api_params["filter[country]"] = country.upper().strip()

            response_data = await make_xbrl_request(f"{XBRL_API_BASE}/filings", params=api_params)

            if not response_data or not response_data.get("data"):
                return []

            # Process included entities
            included_entities = {}
            for item in response_data.get("included", []):
                if item.get("type") == "entities":
                    included_entities[item["id"]] = item.get("attributes", {})

            # Process filings
            filings_list = []
            for filing in response_data["data"]:
                try:
                    attributes = filing.get("attributes", {})
                    
                    # Get entity information
                    entity_name = "Unknown Entity"
                    relationships = filing.get("relationships", {})
                    entity_rel = relationships.get("entity", {}).get("data", {})
                    entity_id = entity_rel.get("id")
                    
                    if entity_id and entity_id in included_entities:
                        entity_name = included_entities[entity_id].get("name", "Unknown Entity")

                    # Process date
                    processed_date = attributes.get('processed', '')
                    if processed_date and 'T' in processed_date:
                        processed_date = processed_date.split('T')[0]
                    else:
                        processed_date = None

                    filings_list.append({
                        "id": filing.get("id"),
                        "entity_name": entity_name,
                        "processed_date": processed_date,
                        "country": attributes.get('country'),
                        "report_url": attributes.get('report_url'),
                        "errors_count": attributes.get('errors_count', 0),
                        "warnings_count": attributes.get('warnings_count', 0),
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing filing: {e}")
                    continue

            logger.info(f"Returning {len(filings_list)} filings")
            return filings_list

        except Exception as e:
            logger.error(f"Error in get_filings: {e}")
            raise

    @mcp.tool()
    async def get_filing(filing_id: str) -> Dict[str, Any]:
        """
        Retrieves a specific filing by its ID.

        Args:
            filing_id: The unique identifier of the filing.
        """
        try:
            logger.info(f"get_filing: {filing_id}")
            
            api_params = {"include": "entity"}
            url = f"{XBRL_API_BASE}/filings/{filing_id}"
            
            response_data = await make_xbrl_request(url, params=api_params)

            if not response_data or not response_data.get("data"):
                raise Exception(f"Filing with ID '{filing_id}' not found")

            filing = response_data["data"]
            attributes = filing.get("attributes", {})

            # Find entity information
            entity_name = "Unknown Entity"
            for item in response_data.get("included", []):
                if item.get("type") == "entities":
                    entity_name = item.get("attributes", {}).get("name", "Unknown Entity")
                    break

            # Process date
            processed_date = attributes.get('processed', '')
            if processed_date and 'T' in processed_date:
                processed_date = processed_date.split('T')[0]
            else:
                processed_date = None

            return {
                "id": filing.get("id"),
                "entity_name": entity_name,
                "processed_date": processed_date,
                "country": attributes.get('country'),
                "report_url": attributes.get('report_url'),
                "errors_count": attributes.get('errors_count', 0),
                "warnings_count": attributes.get('warnings_count', 0),
            }

        except Exception as e:
            logger.error(f"Error in get_filing: {e}")
            raise

    @mcp.tool()
    async def get_entity(entity_id: str) -> Dict[str, Any]:
        """
        Retrieves details for a specific entity by its ID.

        Args:
            entity_id: The unique identifier of the entity.
        """
        try:
            logger.info(f"get_entity: {entity_id}")
            
            url = f"{XBRL_API_BASE}/entities/{entity_id}"
            response_data = await make_xbrl_request(url)

            if not response_data or not response_data.get("data"):
                raise Exception(f"Entity with ID '{entity_id}' not found")

            entity = response_data["data"]
            attributes = entity.get("attributes", {})

            return {
                "id": entity.get("id"),
                "name": attributes.get("name"),
                "lei": attributes.get("lei"),
                "cik": attributes.get("cik"),
                "sic": attributes.get("sic"),
            }

        except Exception as e:
            logger.error(f"Error in get_entity: {e}")
            raise

    # Log successful setup
    logger.info("MCP server setup complete")

except Exception as e:
    sys.stderr.write(f"Setup failed: {e}\n")
    sys.stderr.flush()
    sys.exit(1)

finally:
    # Always restore stdout before running MCP
    sys.stdout = _original_stdout

# Now run the server
if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)