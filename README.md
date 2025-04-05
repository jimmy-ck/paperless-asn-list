# Paperless ASN List Exporter

This Python script interacts with the [Paperless-ngx API](https://docs.paperless-ngx.com/api/) to fetch documents within a specified ASN range, group them by custom fields (e.g., "Lagerort"), and export the results to a tab-separated CSV file.

## Features

- Fetches documents from Paperless-ngx within a specified ASN range.
- Groups documents by a custom field (e.g., "Lagerort").
- Supports secondary grouping by either correspondents or ASNs.
- Sorts groups alphabetically (case-insensitive) and ASNs numerically.
- Exports the grouped data to a dynamically named CSV file.
- Uses a separate credentials file (`credentials.py`) to securely store API URL and token.

## Prerequisites

- Python 3.6 or later
- Paperless-ngx instance with API access enabled
- Virtual environment (`venv`) for dependency management

## Setup Instructions

1. Clone this repository:
    ```
    git clone <repository-url>
    cd <repository-folder>
    ```

2. Create and activate a virtual environment:
    ```
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Create a `credentials.py` file (excluded from Git):
    ```
    # credentials.py
    API_URL = "http://your-paperless-instance:7000/api"
    API_TOKEN = "your_api_token_here"
    ```

5. Run the script:
    ```
    python main.py
    ```

## Parameters

The following parameters can be adjusted in the script:

| Parameter                  | Description                                                                 | Default Value     |
|----------------------------|-----------------------------------------------------------------------------|-------------------|
| `ASN_FROM`                 | Minimum ASN value to query documents from                                   | 1                 |
| `ASN_TO`                   | Maximum ASN value to query documents up to                                  | 671               |
| `CUSTOM_FIELD_ID`          | ID of the custom field used for primary grouping (e.g., "Storage box")      | 3                 |
| `SECONDARY_GROUP_BY_FIELD` | Field used for secondary grouping (`"Correspondent"` or `"ASN"`)            | `"Correspondent"` |

## Output

The script generates a tab-separated CSV file with the following columns:

1. **Storage Box**: The custom field label (e.g., "Box 1").
2. **ASN**: Archive Serial Number of the document.
3. **Correspondent**: Name of the correspondent associated with the document.
4. **Title**: Title of the document.
5. **Date**: Creation date of the document.

The CSV filename is dynamically generated based on the timestamp, ASN range, and grouping logic, e.g.:
    ```
    20250405_161700_Lagerort_grouped_by_Correspondent_ASN_1-671.csv
    ```

### Example Output

#### Grouped by Storage box → Correspondent → ASN:
| Lagerort | ASN  | Correspondent  | Title         | Date       |
|----------|------|----------------|---------------|------------|
| Box 1    | 102  | Alice Corp     | Receipt Feb   | 2025-02-01 |
| Box 1    | 101  | Alice Corp     | Invoice Jan   | 2025-01-01 |
| Box 1    | 103  | Bob Inc.       | Contract Mar  | 2025-03-01 |
| Box 2    | 105  | Charlie Ltd.   | Report Apr    | 2025-04-01 |
| Box 2    | 104  | Charlie Ltd.   | Memo May      | 2025-05-01 |

## Notes

1. Ensure that your Paperless-ngx instance is accessible via the provided API URL.
2. Use `.gitignore` to exclude sensitive files like `credentials.py` and temporary files like `.csv`.

## License

This project is licensed under the MIT License.