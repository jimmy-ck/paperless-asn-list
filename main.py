import csv
from datetime import datetime
import requests
import argparse

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

def export_correspondents_list(grouped_by_custom_field, correspondents, asn_from, asn_to):
    """
    Exports a list of all correspondents with their documents, sorted by correspondent and date.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get all documents and group by correspondent
    all_docs = []
    for group_key, docs in grouped_by_custom_field.items():
        for doc in docs:
            doc['storage_box'] = group_key  # Add storage box info to document
            all_docs.append(doc)
    
    # Calculate actual min and max ASN from the documents
    asn_values = [int(doc["archive_serial_number"]) for doc in all_docs]
    actual_min_asn = min(asn_values) if asn_values else asn_from
    actual_max_asn = max(asn_values) if asn_values else asn_to
    
    filename = f"{timestamp}_grouped_by_Correspondent_ASN_{actual_min_asn}-{actual_max_asn}.csv"
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        
        # Write header row
        writer.writerow(["Correspondent", "Date", "Title", "StorageBox", "ASN"])
        
        # Group by correspondent
        correspondent_groups = {}
        for doc in all_docs:
            corr_name = correspondents.get(doc["correspondent"], "Unknown")
            if corr_name not in correspondent_groups:
                correspondent_groups[corr_name] = []
            correspondent_groups[corr_name].append(doc)
        
        # Sort correspondents alphabetically (case-insensitive)
        for corr_name in sorted(correspondent_groups.keys(), key=lambda x: x.lower()):
            docs = correspondent_groups[corr_name]
            
            # Sort by date (ascending)
            docs.sort(key=lambda doc: doc["created_date"])
            
            for doc in docs:
                writer.writerow([
                    corr_name,
                    doc["created_date"],
                    doc["title"],
                    doc['storage_box'],
                    doc["archive_serial_number"]
                ])
    
    print(f"Correspondents list exported to {filename}")
    return filename


def export_storage_box_by_correspondent(grouped_by_custom_field, correspondents, asn_from, asn_to):
    """
    Exports one list per storage box, grouped by correspondent and sorted by date.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = []
    
    # Sort storage boxes alphabetically (case-insensitive)
    for storage_box in sorted(grouped_by_custom_field.keys(), key=lambda x: x.lower()):
        docs = grouped_by_custom_field[storage_box]
        
        # Find min and max ASN in this storage box
        min_asn = min([int(doc["archive_serial_number"]) for doc in docs])
        max_asn = max([int(doc["archive_serial_number"]) for doc in docs])
        
        filename = f"{timestamp}_{storage_box}_grouped_by_Correspondent_ASN_{min_asn}-{max_asn}.csv"
        
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            
            # Write header row
            writer.writerow(["StorageBox", "Correspondent", "Date", "Title", "ASN"])
            
            # Group by correspondent
            correspondent_groups = {}
            for doc in docs:
                corr_name = correspondents.get(doc["correspondent"], "Unknown")
                if corr_name not in correspondent_groups:
                    correspondent_groups[corr_name] = []
                correspondent_groups[corr_name].append(doc)
            
            # Sort correspondents alphabetically (case-insensitive)
            for corr_name in sorted(correspondent_groups.keys(), key=lambda x: x.lower()):
                corr_docs = correspondent_groups[corr_name]
                
                # Sort by date (ascending)
                corr_docs.sort(key=lambda doc: doc["created_date"])
                
                for doc in corr_docs:
                    writer.writerow([
                        storage_box,
                        corr_name,
                        doc["created_date"],
                        doc["title"],
                        doc["archive_serial_number"]
                    ])
        
        filenames.append(filename)
        print(f"Storage box list (by correspondent) exported to {filename}")
    
    return filenames

def export_storage_box_by_asn(grouped_by_custom_field, correspondents, asn_from, asn_to):
    """
    Exports one list per storage box, sorted by ASN.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = []
    
    # Sort storage boxes alphabetically (case-insensitive)
    for storage_box in sorted(grouped_by_custom_field.keys(), key=lambda x: x.lower()):
        docs = grouped_by_custom_field[storage_box]
        
        # Find min and max ASN in this storage box
        min_asn = min([int(doc["archive_serial_number"]) for doc in docs])
        max_asn = max([int(doc["archive_serial_number"]) for doc in docs])
        
        filename = f"{timestamp}_{storage_box}_grouped_by_ASN_{min_asn}-{max_asn}.csv"
        
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            
            # Write header row
            writer.writerow(["StorageBox", "ASN", "Correspondent", "Title", "Date"])
            
            # Sort by ASN (ascending)
            docs.sort(key=lambda doc: int(doc["archive_serial_number"]))
            
            for doc in docs:
                correspondent_name = correspondents.get(doc["correspondent"], "Unknown")
                writer.writerow([
                    storage_box,
                    doc["archive_serial_number"],
                    correspondent_name,
                    doc["title"],
                    doc["created_date"]
                ])
        
        filenames.append(filename)
        print(f"Storage box list (by ASN) exported to {filename}")
    
    return filenames

if __name__ == "__main__":
    # Define ASN range and grouping options
    parser = argparse.ArgumentParser(description='Process ASN and Custom Field ID.')
    parser.add_argument('--asn_from', type=int, default=1, help='Minimum ASN value (default: 1)')
    parser.add_argument('--asn_to', type=int, default=9999, help='Maximum ASN value (default: 9999)')
    parser.add_argument('--custom_field_id', type=int, default=3, help='Custom field ID for StorageBox (default: 3)')
    args = parser.parse_args()

    try:
        # Fetch possible labels for StorageBox
        storage_box_label_mapping = fetch_custom_field_labels(args.custom_field_id)

        # Fetch correspondents and filtered documents by ASN range
        correspondents_map = fetch_correspondents()
        filtered_documents_list = fetch_documents(args.asn_from, args.asn_to)

        # Group by StorageBox (custom field)
        primary_grouped_docs = group_documents_by_custom_field(filtered_documents_list, args.custom_field_id, storage_box_label_mapping)

        # Export all three list types
        export_correspondents_list(primary_grouped_docs, correspondents_map, args.asn_from, args.asn_to)
        export_storage_box_by_correspondent(primary_grouped_docs, correspondents_map, args.asn_from, args.asn_to)
        export_storage_box_by_asn(primary_grouped_docs, correspondents_map, args.asn_from, args.asn_to)
    
    except Exception as e:
        print(f"Error: {e}")