# XBRL Filings MCP Server

This repository contains a Python-based MCP (Machine-Readable Co-pilot) server that provides tools to query the `filings.xbrl.org` database for XBRL filings.

## Features

-   Fetch recent XBRL filings, with options to filter by country.
-   Retrieve detailed information for a specific filing.
-   Look up details for a specific entity.
-   Returns company names and LEIs along with filing data.

## Prerequisites

-   Python 3.10 or higher

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    The server uses `fastmcp` and `httpx`. You can install them using pip:
    ```bash
    pip install "mcp[cli]" httpx
    ```

## Running the Server

To run the server, execute the script from your terminal:
```bash
python3 xbrl_mcp_server.py
```
The server runs over standard input/output (stdio) and will listen for requests from a connected MCP client.

## API Tools

The server exposes the following tools to an MCP client:

### `get_filings`

Get recent XBRL filings from the `filings.xbrl.org` database.

-   **Args:**
    -   `country` (Optional[str]): The two-letter ISO country code to filter by (e.g., `US`, `GB`).
    -   `page_size` (int): The number of filings to return. Defaults to `5`.
    -   `page_number` (int): The page number to retrieve. Defaults to `1`.
-   **Returns:** A list of filing objects.

### `get_filing`

Retrieves a specific filing by its ID.

-   **Args:**
    -   `filing_id` (str): The unique identifier of the filing.
-   **Returns:** A single filing object.

### `get_entity`

Retrieves details for a specific entity by its ID.

-   **Args:**
    -   `entity_id` (str): The unique identifier of the entity.
-   **Returns:** An entity object with details like name, LEI, CIK, and SIC.

## Data Source

This server is a wrapper around the official XBRL Filings API. For more information about the data, visit [filings.xbrl.org](https://filings.xbrl.org).
