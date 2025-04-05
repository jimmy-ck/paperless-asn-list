# Paperless ASN List Exporter

This Python script interacts with the [Paperless-ngx API](https://docs.paperless-ngx.com/api/) to fetch documents within a specified ASN range, group them by custom fields (e.g., "StorageBox"), and export the results to a tab-separated CSV file.

## Features

- Fetches documents from a selfhosted Paperless-ngx instance within a specified ASN range.
- Groups documents by a custom field (e.g., "StorageBox").
- Groups by correspondents and ASNs with specific sorting into three separate lists for easy physical retrieval of your documents in case of a server breakdown.
- Exports the grouped data to a dynamically named CSV files, which can be printed out.

## Prerequisites

- **This script currently assumes a prepopulated custom data field in your Paperless-ngx instance configured as field type `select`, which is used to document physical storage location of documents** (please refer to [Paperless-ngx Basic Usage](https://docs.paperless-ngx.com/usage/#custom-fields))
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
    API_URL = "http://your-paperless-instance:port-number/api"
    API_TOKEN = "your_api_token_here"
    ```

5. Run the script:
    ```
    python main.py
    ```

## Parameters

The following parameters can be adjusted in the script:

| Parameter                  | Description                                                                 | Preset Value     |
|----------------------------|-----------------------------------------------------------------------------|-------------------|
| `ASN_FROM`                 | Minimum ASN value to query documents from                                   | 1                 |
| `ASN_TO`                   | Maximum ASN value to query documents up to                                  | 999               |
| `CUSTOM_FIELD_ID`          | ID of the custom field used for primary grouping (e.g., "StorageBox")       | 3                 |

## Output lists

This script generates three tab-separated CSV files with the following columns.
The idea behind these lists is to physically attach it to containers/boxes of documents. In case of a breakdown of your Paperless-ngx instance you should be able to look up where a specific document resides in this box – all analogue.

### Correspondents → to look up storage box and ASN

> In which box is my document? And what is it's ASN = location? 

Outputs one list for all correspondents assigned to documents which have an ASN: `20250405_161700_grouped_by_Correspondent_ASN_1-275.csv`



This list allows you to identify a document of interest by scrolling through the correspondents list, narrowing down the date and looking up the storage box where you document resides in. Noting the ASN you can directly find it in this specific box, since it should physically be sorted by ASN.

#### Example output
*"↓" are displayed in doc for illustrative purposes only*

1. **Correspondent**: Grouped and sorted case-insensitive alphabetically. Name of the correspondent associated with the document.
2. **Date**: Creation date of the document. Sorted old to new.
3. **Title**: Title of the document.
4. **StorageBox**: The custom field label (e.g., "Box 1").
5. **ASN**: Archive Serial Number of the document.

| Correspondent ↓ | Date ↓     | Title         | StorageBox | ASN  |
|-----------------|------------|---------------|------------|------|
| Alice Corp      | 2025-01-01 | Receipt Feb   | Box 1      | 2    |
| Alice Corp      | 2025-02-01 | Invoice Jan   | Box 1      | 1    |
| Alice Corp      | 2025-03-01 | Invoice Feb   | Box 2      | 6    |
| Bob Inc.        | 2025-03-01 | Contract Mar  | Box 1      | 4    |
| Charlie Ltd.    | 2025-04-01 | Report Apr    | Box 2      | 3    |
| Charlie Ltd.    | 2025-05-01 | Memo May      | Box 2      | 5    |

### Storage box (correspondents) → to look up ASN in a specific storage box

> My document is in this box: What is the document's ASN = location?

Outputs $n$ lists for $n$ storage boxes.
```
20250405_161700_Box1_grouped_by_Correspondent_ASN_1-123.csv
20250405_161700_Box2_grouped_by_Correspondent_ASN_123-255.csv
20250405_161700_Box3_grouped_by_Correspondent_ASN_256-275.csv
```

These lists allow you to identify a document of interest which is known to be in the corresponding box by scrolling through the correspondents list, narrowing down the date and looking up the ASN of your document. Since your box should physically be sorted by ASN it is easy to locate the document.

#### Example output
*"↓" are displayed in doc for illustrative purposes only*

1. **StorageBox**: Grouped and sorted case-insensitive alphabetically. The custom field label (e.g., "Box 1").
2. **Correspondent**: Grouped and sorted case-insensitive alphabetically. Name of the correspondent associated with the document.
3. **Date**: Creation date of the document. Sorted old to new.
4. **Title**: Title of the document.
5. **ASN**: Archive Serial Number of the document.

| StorageBox ↓ | Correspondent ↓ | Date ↓     | Title         | ASN |
|--------------|-----------------|------------|---------------|-----|
| Box 1        | Alice Corp      | 2025-01-01 | Receipt Feb   | 2   |
| Box 1        | Alice Corp      | 2025-02-01 | Invoice Jan   | 1   |
| Box 1        | Bob Inc.        | 2025-03-01 | Contract Mar  | 4   |
| Box 2        | Alice Corp      | 2025-03-01 | Invoice Feb   | 6   |
| Box 2        | Charlie Ltd.    | 2025-04-01 | Report Apr    | 3   |
| Box 2        | Charlie Ltd.    | 2025-05-01 | Memo May      | 5   |

### Storage box (ASN) → to see whats in a specific box
> What is in this box? 

Outputs $n$ lists for $n$ storage boxes.
```
20250405_161700_Box1_grouped_by_ASN_1-123.csv
20250405_161700_Box2_grouped_by_ASN_123-255.csv
20250405_161700_Box3_grouped_by_ASN_256-275.csv
```

This list is a simple ASN-sorted list of a boxes content. It just reflects the physical sorting of the actual box.

#### Example output
*"↓" are displayed in doc for illustrative purposes only*

1. **StorageBox**: Grouped and sorted case-insensitive alphabetically. The custom field label (e.g., "Box 1").
2. **ASN**: Archive Serial Number of the document. Sorted ascending.
3. **Correspondent**: Name of the correspondent associated with the document.
4. **Title**: Title of the document.
5. **Date**: Creation date of the document.

| StorageBox ↓ | ASN ↓ | Correspondent  | Title         | Date       |
|--------------|-------|----------------|---------------|------------|
| Box 1        | 1     | Alice Corp     | Receipt Feb   | 2025-02-01 |
| Box 1        | 2     | Alice Corp     | Invoice Jan   | 2025-01-01 |
| Box 1        | 4     | Bob Inc.       | Contract Mar  | 2025-03-01 |
| Box 2        | 3     | Charlie Ltd.   | Report Apr    | 2025-04-01 |
| Box 2        | 5     | Charlie Ltd.   | Memo May      | 2025-05-01 |
| Box 2        | 6     | Alice Corp     | Invoice Feb   | 2025-03-01 |

## License

This project is licensed under the MIT License.