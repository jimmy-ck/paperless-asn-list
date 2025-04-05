# Paperless ASN List Exporter

This Python script interacts with the [Paperless-ngx API](https://docs.paperless-ngx.com/api/) to fetch documents within a specified ASN range, group them by custom fields (e.g., "StorageBox"), and export the results to a tab-separated CSV file.

## Features

- Fetches documents from a selfhosted Paperless-ngx instance within a specified ASN range.
- Groups documents by a custom field (e.g., "StorageBox").
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
    git clone https://github.com/jimmy-ck/paperless-asn-list.git
    cd paperless-asn-list
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
| `ASN_TO`                   | Maximum ASN value to query documents up to                                  | 999               |
| `CUSTOM_FIELD_ID`          | ID of the custom field used for primary grouping (e.g., "StorageBox")       | 3                 |

## Output

The script generates two tab-separated CSV files with the following columns.

Grouped by ASN:
1. **StorageBox**: Grouped and sorted case-insensitive alphabetically. The custom field label (e.g., "Box 1").
2. **ASN**: Archive Serial Number of the document.
3. **Correspondent**: Name of the correspondent associated with the document.
4. **Title**: Title of the document.
5. **Date**: Creation date of the document.

Grouped by correspondents:
1. **StorageBox**: Grouped and sorted case-insensitive alphabetically. The custom field label (e.g., "Box 1").
2. **Correspondent**: Grouped. Name of the correspondent associated with the document. Sorted case-insensitive alphabetically.
3. **Date**: Creation date of the document. Sorted old to new.
4. **Title**: Title of the document.
5. **ASN**: Archive Serial Number of the document.

The CSV filename is dynamically generated based on the timestamp, ASN range, and grouping logic, e.g.:
    ```
    20250405_161700_StorageBox_grouped_by_Correspondent_ASN_1-671.csv
    ```

### Example Output

#### Grouped by StorageBox → Correspondent → ASN:
| StorageBox | ASN  | Correspondent  | Title         | Date       |
|----------|------|----------------|---------------|------------|
| Box 1    | 1    | Alice Corp     | Receipt Feb   | 2025-02-01 |
| Box 1    | 2    | Alice Corp     | Invoice Jan   | 2025-01-01 |
| Box 1    | 3    | Bob Inc.       | Contract Mar  | 2025-03-01 |
| Box 2    | 4    | Charlie Ltd.   | Report Apr    | 2025-04-01 |
| Box 2    | 5    | Charlie Ltd.   | Memo May      | 2025-05-01 |

## Notes

1. Ensure that your Paperless-ngx instance is accessible via the provided API URL.
2. Use `.gitignore` to exclude sensitive files like `credentials.py` and temporary files like `.csv`.

## License

This project is licensed under the MIT License.