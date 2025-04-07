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
    url = f"{API_URL}/custom_fields/{custom_field_id}/"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch custom field labels: {response.text}")
    content = response.json()
    select_options = content.get("extra_data", {}).get("select_options", [])
    return {
        "name": content["name"],
        "options": {option["id"]: option["label"] for option in select_options}
    }

def fetch_correspondents():
    """
    Fetches all correspondents from the Paperless-ngx API.

    Returns:
        dict: Mapping of correspondent IDs to their names.
    """
    url = f"{API_URL}/correspondents/"
    correspondents_map = {}
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch correspondents: {response.text}")
        content = response.json()
        for correspondent in content["results"]:
            correspondents_map[correspondent["id"]] = correspondent["name"]
        url = content["next"]
    return correspondents_map

def fetch_documents(asn_from, asn_to):
    """
    Fetches documents within a specific ASN range from the Paperless-ngx API
    and calculates the min and max ASN values.

    Args:
        asn_from (int): Minimum ASN value.
        asn_to (int): Maximum ASN value.

    Returns:
        tuple: (list of document dictionaries, min ASN, max ASN)
    """
    url = f"{API_URL}/documents/?archive_serial_number__gte={asn_from}&archive_serial_number__lte={asn_to}"
    documents = []
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch documents: {response.text}")
        content = response.json()
        documents.extend(content["results"])
        url = content["next"]
    asn_values = [int(doc["archive_serial_number"]) for doc in documents]
    actual_min_asn = min(asn_values) if asn_values else asn_from
    actual_max_asn = max(asn_values) if asn_values else asn_to
    return documents, actual_min_asn, actual_max_asn

def group_documents_by_custom_field(documents, custom_field_name, custom_field_id, label_mapping):
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
        custom_fields = document.get("custom_fields", [])
        group_key = "Unknown"
        for field in custom_fields:
            if field["field"] == custom_field_id:
                group_key = label_mapping["options"].get(field["value"], "Unknown")
                break
        grouped_documents.setdefault(group_key, []).append(document)
    return grouped_documents

def export_correspondent_documents_list(grouped_by_custom_field, correspondents, asn_from, asn_to, is_grouped, custom_field_name="StorageBox"):
    """
    Exports a list containing all documents in range,
    either primary-grouped by custom field or primary-ungrouped
    and always secondary-grouped by correspondent.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_grouped_by_Correspondent_ASN_{asn_from}-{asn_to}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow([
            "Correspondent",
            "Date", "Title",
            *(custom_field_name if is_grouped else []),
            "ASN"])
        all_docs = []
        
        for group_key, docs in (grouped_by_custom_field.items() if is_grouped else [("", grouped_by_custom_field)]):
            for doc in docs:
                doc['storage_box'] = group_key
                all_docs.append(doc)
        
        correspondent_groups = {}
        
        for doc in all_docs:
            name = correspondents.get(doc["correspondent"], "Unknown")
            correspondent_groups.setdefault(name, []).append(doc)
        
        for name in sorted(correspondent_groups.keys(), key=str.lower):
            docs = sorted(correspondent_groups[name], key=lambda d: d["created_date"])
            for doc in docs:
                writer.writerow([
                    name,
                    doc["created_date"],
                    doc["title"],
                    *([doc['storage_box']] if is_grouped else []),
                    doc["archive_serial_number"]
                ])
    print(f"Documents list exported to {filename}")
    return filename

def export_custom_field_by_correspondent(custom_field_name, grouped_by_custom_field, correspondents):
    """
    Exports one list per storage box, grouped by correspondent and sorted by date.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = []
    for box in sorted(grouped_by_custom_field.keys(), key=str.lower):
        docs = grouped_by_custom_field[box]
        min_asn = min(int(doc["archive_serial_number"]) for doc in docs)
        max_asn = max(int(doc["archive_serial_number"]) for doc in docs)

        filename = f"{timestamp}_{box}_grouped_by_Correspondent_ASN_{min_asn}-{max_asn}.csv"

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([
                custom_field_name,
                "Correspondent",
                "Date",
                "Title",
                "ASN"])

            corr_groups = {}

            for doc in docs:
                name = correspondents.get(doc["correspondent"], "Unknown")
                corr_groups.setdefault(name, []).append(doc)
            for name in sorted(corr_groups.keys(), key=str.lower):
                sorted_docs = sorted(corr_groups[name], key=lambda d: d["created_date"])
                for doc in sorted_docs:
                    writer.writerow([
                        box,
                        name,
                        doc["created_date"],
                        doc["title"],
                        doc["archive_serial_number"]])
        filenames.append(filename)
        print(f"Storage box list (by correspondent) exported to {filename}")
    return filenames

def export_custom_field_by_asn(custom_field_name, grouped_by_custom_field, correspondents):
    """
    Exports one list per storage box, sorted by ASN.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = []
    for box in sorted(grouped_by_custom_field.keys(), key=str.lower):
        docs = grouped_by_custom_field[box]
        min_asn = min(int(doc["archive_serial_number"]) for doc in docs)
        max_asn = max(int(doc["archive_serial_number"]) for doc in docs)

        filename = f"{timestamp}_{box}_grouped_by_ASN_{min_asn}-{max_asn}.csv"

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([
                custom_field_name,
                "ASN",
                "Correspondent",
                "Title",
                "Date"])

            docs.sort(key=lambda d: int(d["archive_serial_number"]))

            for doc in docs:
                name = correspondents.get(doc["correspondent"], "Unknown")
                writer.writerow([
                    box,
                    doc["archive_serial_number"],
                    name,
                    doc["title"],
                    doc["created_date"]])
        filenames.append(filename)
        print(f"Storage box list (by ASN) exported to {filename}")
    return filenames

def run_export_without_custom_field(asn_from, asn_to, correspondents_map):
    documents, actual_min_asn, actual_max_asn = fetch_documents(asn_from, asn_to)
    
    export_correspondent_documents_list(
        grouped_by_custom_field=documents,
        correspondents=correspondents_map,
        asn_from=actual_min_asn,
        asn_to=actual_max_asn,
        is_grouped=False
    )

def run_export_with_custom_field(asn_from, asn_to, custom_field_id, correspondents_map):
    documents, actual_min_asn, actual_max_asn = fetch_documents(asn_from, asn_to)
    label_mapping = fetch_custom_field_labels(custom_field_id)
    
    grouped_docs = group_documents_by_custom_field(
        documents=documents,
        custom_field_name=label_mapping["name"],
        custom_field_id=custom_field_id,
        label_mapping=label_mapping
    )
    
    export_correspondent_documents_list(
        grouped_by_custom_field=grouped_docs,
        correspondents=correspondents_map,
        asn_from=actual_min_asn,
        asn_to=actual_max_asn,
        is_grouped=True,
        custom_field_name=label_mapping["name"]
    )
    
    export_custom_field_by_correspondent(
        custom_field_name=label_mapping["name"],
        grouped_by_custom_field=grouped_docs,
        correspondents=correspondents_map
    )
    
    export_custom_field_by_asn(
        custom_field_name=label_mapping["name"],
        grouped_by_custom_field=grouped_docs,
        correspondents=correspondents_map
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export documents from Paperless-ngx")
    parser.add_argument("--asn_from", type=int, default=1, help="Minimum ASN value (default: 1)")
    parser.add_argument("--asn_to", type=int, default=9999, help="Maximum ASN value (default: 9999)")
    parser.add_argument("--custom_field_id", type=int, default=3, help="Custom field ID for grouping (default: 3)")
    parser.add_argument("--no_custom_field", action="store_true", help="Deactivate grouping by custom field")
    args = parser.parse_args()

    correspondents_map = fetch_correspondents()
    if args.no_custom_field:
        run_export_without_custom_field(
            asn_from=args.asn_from,
            asn_to=args.asn_to,
            correspondents_map=correspondents_map
        )
    else:
        run_export_with_custom_field(
            asn_from=args.asn_from,
            asn_to=args.asn_to,
            custom_field_id=args.custom_field_id,
            correspondents_map=correspondents_map
        )