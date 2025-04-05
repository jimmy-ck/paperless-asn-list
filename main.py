import csv
from datetime import datetime
import requests
# Import credentials
from credentials import API_URL, API_TOKEN

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_custom_field_labels(custom_field_id):
    """
    Fetches all possible labels for a custom field with a 'select' data type.

    Args:
        custom_field_id (int): ID of the custom field.

    Returns:
        dict: Mapping of value IDs to their labels.
    """
    custom_field_url = f"{API_URL}/custom_fields/{custom_field_id}/"
    response = requests.get(custom_field_url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch custom field labels: {response.text}")
    
    content = response.json()
    select_options = content.get("extra_data", {}).get("select_options", [])
    return {option["id"]: option["label"] for option in select_options}


def fetch_correspondents():
    """
    Fetches all correspondents from the Paperless-ngx API.

    Returns:
        dict: Mapping of correspondent IDs to their names.
    """
    correspondents_url = f"{API_URL}/correspondents/"
    correspondents_map = {}

    next_url = correspondents_url
    while next_url:
        response = requests.get(next_url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch correspondents: {response.text}")
        
        content = response.json()
        for correspondent in content["results"]:
            correspondents_map[correspondent["id"]] = correspondent["name"]
        
        next_url = content["next"]

    return correspondents_map


def fetch_documents(asn_from, asn_to):
    """
    Fetches documents within a specific ASN range from the Paperless-ngx API.

    Args:
        asn_from (int): Minimum ASN value.
        asn_to (int): Maximum ASN value.

    Returns:
        list: List of document dictionaries.
    """
    documents_url = f"{API_URL}/documents/?archive_serial_number__gte={asn_from}&archive_serial_number__lte={asn_to}"
    documents = []

    next_url = documents_url
    while next_url:
        response = requests.get(next_url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch documents: {response.text}")
        
        content = response.json()
        documents.extend(content["results"])
        
        next_url = content["next"]

    return documents


def group_documents_by_custom_field(documents, custom_field_id, label_mapping):
    """
    Groups documents by a specified custom field label.

    Args:
        documents (list): List of document dictionaries.
        custom_field_id (int): ID of the custom field to group by.
        label_mapping (dict): Mapping of value IDs to their labels.

    Returns:
        dict: Grouped documents where keys are custom field labels and values are lists of document dictionaries.
    """
    grouped_documents = {}

    for document in documents:
        # Extract the value of the custom field
        custom_fields = document.get("custom_fields", [])
        group_key = "Unknown"
        
        for field in custom_fields:
            if field["field"] == custom_field_id:
                group_key = label_mapping.get(field["value"], "Unknown")
                break

        if group_key not in grouped_documents:
            grouped_documents[group_key] = []
        
        grouped_documents[group_key].append(document)

    return grouped_documents


def group_within_custom_field(documents, correspondents, group_by):
    """
    Groups documents within a custom field group by another specified field.

    Args:
        documents (list): List of document dictionaries.
        correspondents (dict): Mapping of correspondent IDs to names.
        group_by (str): Field to group within the custom field. Options: "Correspondent", "ASN".

    Returns:
        dict: Grouped documents where keys are secondary group values and values are lists of document dictionaries.
    """
    grouped_documents = {}

    for document in documents:
        if group_by == "Correspondent":
            key = correspondents.get(document["correspondent"], "Unknown")
        elif group_by == "ASN":
            key = str(document["archive_serial_number"])
        else:
            key = str(document["id"])

        if key not in grouped_documents:
            grouped_documents[key] = []
        
        grouped_documents[key].append(document)

    return grouped_documents


def print_grouped_documents(grouped_by_custom_field, correspondents, secondary_group_by):
    """
    Prints grouped documents based on primary and secondary grouping criteria.

    Args:
        grouped_by_custom_field (dict): Documents grouped by the primary custom field.
        correspondents (dict): Mapping of correspondent IDs to names.
        secondary_group_by (str): Field used for secondary grouping. Options: "Correspondent", "ASN".
    """
    for group_key, docs in grouped_by_custom_field.items():
        print(f"\n{group_key}")  # Print Lagerort or other custom field label

        if secondary_group_by == "ASN":
            # Sort and print all documents directly by ASN
            docs.sort(key=lambda doc: int(doc["archive_serial_number"]))
            for doc in docs:
                # Use the correspondent name if available; otherwise, print "Unknown"
                correspondent_name = correspondents.get(doc["correspondent"], "Unknown")
                print(f"ASN: {doc['archive_serial_number']} | Correspondent: {correspondent_name} | Title: {doc['title']} | Date: {doc['created_date']}")
        
        elif secondary_group_by == "Correspondent":
            # Group by Correspondent within Lagerort
            grouped_within_custom_field = group_within_custom_field(docs, correspondents, secondary_group_by)
            for sub_group_key, sub_docs in grouped_within_custom_field.items():
                print(f"\n{secondary_group_by}: {sub_group_key}")  # Print Correspondent name
                sub_docs.sort(key=lambda doc: int(doc["archive_serial_number"]))
                for doc in sub_docs:
                    print(f"ASN: {doc['archive_serial_number']} | Title: {doc['title']} | Date: {doc['created_date']}")


def export_to_csv(grouped_by_custom_field, correspondents, secondary_group_by, asn_from, asn_to):
    """
    Exports grouped data to a tab-separated CSV file.

    Args:
        grouped_by_custom_field (dict): Documents grouped by the primary custom field.
        correspondents (dict): Mapping of correspondent IDs to names.
        secondary_group_by (str): Field used for secondary grouping. Options: "Correspondent", "ASN".
        asn_from (int): Minimum ASN value.
        asn_to (int): Maximum ASN value.
    
    Returns:
        str: Filename of the exported CSV file.
    """
    # Generate a dynamic filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_Lagerort_grouped_by_{secondary_group_by}_ASN_{asn_from}-{asn_to}.csv"

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")

        # Write header row
        writer.writerow(["Lagerort", "ASN", "Correspondent", "Title", "Date"])

        # Sort Lagerort groups alphabetically (case-insensitive) and iterate
        for group_key in sorted(grouped_by_custom_field.keys(), key=lambda x: x.lower()):
            docs = grouped_by_custom_field[group_key]

            if secondary_group_by == "ASN":
                # Sort documents by ASN
                docs.sort(key=lambda doc: int(doc["archive_serial_number"]))
                for doc in docs:
                    correspondent_name = correspondents.get(doc["correspondent"], "Unknown")
                    writer.writerow([
                        group_key,
                        doc["archive_serial_number"],
                        correspondent_name,
                        doc["title"],
                        doc["created_date"]
                    ])
            elif secondary_group_by == "Correspondent":
                # Group documents by Correspondent within Lagerort
                grouped_within_custom_field = group_within_custom_field(docs, correspondents, secondary_group_by)

                # Sort correspondent groups alphabetically (case-insensitive)
                for sub_group_key in sorted(grouped_within_custom_field.keys(), key=lambda x: x.lower()):
                    sub_docs = grouped_within_custom_field[sub_group_key]

                    # Sort documents within each correspondent group by ASN
                    sub_docs.sort(key=lambda doc: int(doc["archive_serial_number"]))
                    
                    for doc in sub_docs:
                        writer.writerow([
                            group_key,
                            doc["archive_serial_number"],
                            sub_group_key,  # Correspondent name
                            doc["title"],
                            doc["created_date"]
                        ])

    print(f"Data exported to {filename}")
    return filename


if __name__ == "__main__":
    # Define ASN range and grouping options
    ASN_FROM = 1  # Minimum ASN value
    ASN_TO = 671  # Maximum ASN value
    CUSTOM_FIELD_ID = 3  # Custom field ID for Lagerort
    SECONDARY_GROUP_BY_FIELD = "Correspondent"  # Options: "Correspondent", "ASN"

    try:
        # Fetch possible labels for Lagerort
        lagerort_label_mapping = fetch_custom_field_labels(CUSTOM_FIELD_ID)

        # Fetch correspondents and filtered documents by ASN range
        correspondents_map = fetch_correspondents()
        filtered_documents_list = fetch_documents(ASN_FROM, ASN_TO)

        # Group by Lagerort (custom field)
        primary_grouped_docs = group_documents_by_custom_field(filtered_documents_list, CUSTOM_FIELD_ID, lagerort_label_mapping)

        # Export results to CSV
        export_to_csv(primary_grouped_docs, correspondents_map, SECONDARY_GROUP_BY_FIELD, ASN_FROM, ASN_TO)
    
    except Exception as e:
        print(f"Error: {e}")