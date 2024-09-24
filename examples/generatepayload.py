#!/usr/bin/env python3

import random
import json
from datetime import datetime, timedelta

# Helper function to generate random metrics values
def generate_random_metrics():
    return {
        "clientcount.current_month_estimate.type.acme_client": {
            "key": "clientcount.current_month_estimate.type.acme_client",
            "value": random.randint(0, 100),
            "mode": "write"
        },
        "clientcount.current_month_estimate.type.entity": {
            "key": "clientcount.current_month_estimate.type.entity",
            "value": random.randint(0, 1000),
            "mode": "write"
        },
        "clientcount.current_month_estimate.type.nonentity": {
            "key": "clientcount.current_month_estimate.type.nonentity",
            "value": random.randint(0, 600),
            "mode": "write"
        },
        "clientcount.current_month_estimate.type.secret_sync": {
            "key": "clientcount.current_month_estimate.type.secret_sync",
            "value": random.randint(0, 400),
            "mode": "write"
        },
        "clientcount.previous_month_complete.type.acme_client": {
            "key": "clientcount.previous_month_complete.type.acme_client",
            "value": random.randint(0, 100),
            "mode": "write"
        },
        "clientcount.previous_month_complete.type.entity": {
            "key": "clientcount.previous_month_complete.type.entity",
            "value": random.randint(0, 5000),
            "mode": "write"
        },
        "clientcount.previous_month_complete.type.nonentity": {
            "key": "clientcount.previous_month_complete.type.nonentity",
            "value": random.randint(0, 400),
            "mode": "write"
        },
        "clientcount.previous_month_complete.type.secret_sync": {
            "key": "clientcount.previous_month_complete.type.secret_sync",
            "value": random.randint(0, 100),
            "mode": "write"
        }
    }

# Function to generate snapshots over 6 months
def generate_snapshots():
    base_snapshot = {
        "snapshot_version": 2,
        "id": "0001JWAY00BRF8TEXC9CVRHBAC",
        "schema_version": "2.0.0",
        "product": "vault",
        "process_id": "01HP5NJS21HN50FY0CBS0SYGCH",
        "product_version": "1.16.0+ent",
        "license_id": "7d68b16a-74fe-3b9f-a1a7-08cf461fff1c",
        "checksum": 6861637915450723051,
        "metadata": {
            "billing_start": "2023-05-04T00:00:00Z",
            "cluster_id": "16d0ff5b-9d40-d7a7-384c-c9b95320c60e"
        }
    }
    
    start_date = datetime(2024, 1, 1, 0, 0)
    snapshots = []

    # Generate one snapshot per month for 6 months
    for month in range(12):
        for _ in range(5):
            # Vary the timestamp randomly within the month
            timestamp = start_date + timedelta(days=random.randint(1, 28), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            snapshot = base_snapshot.copy()
            snapshot["timestamp"] = timestamp.isoformat() + "-08:00"  # Simulating the UTC offset
            snapshot["metrics"] = generate_random_metrics()
            snapshots.append(snapshot)
        # Move to the next month
        start_date += timedelta(days=30)

    return snapshots

# Metadata to be added at the start
metadata = {
    "version": "2",
    "mode": "manual",
    "timestamp": "2024-08-27T22:43:41.54152137Z",
    "signature": "c51a418a943667a35b6b4b6f014ba5bd94530181ffe7344988bbbf9d3cec6854",
    "checksum": 2919400994065523000,
    "snapshots": generate_snapshots()
}

# Save the JSON payload to a file
with open('snapshots.json', 'w') as json_file:
    json.dump(metadata, json_file, indent=2)

print("JSON file saved as snapshots.json")
