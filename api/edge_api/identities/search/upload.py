import datetime
import os
import random
import shutil
import uuid

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Number of items (traits) to be created
num_items = 5000000

# Initialize Boto3 clients
dynamodb = boto3.client("dynamodb", region_name="eu-west-2")
s3_client = boto3.client("s3")

# DynamoDB table and S3 bucket details
table_name = "flagsmith_identities"
bucket_name = "identity-by-traits-data"
s3_prefix = "traits/"

# Path to the local JSON file
json_file_path = "dynamodb_format.json"

# Clean up the local output directory if it exists
output_dir = "partitioned_and_bucketed_data"
shutil.rmtree(output_dir, ignore_errors=True)
os.makedirs(output_dir, exist_ok=True)

# Number of buckets for bucketing by trait_value
num_buckets = 8

# Global counter
counter = 0

# Define the expected schema
expected_columns = {
    "identity_id": str,
    "trait_value": str,
    "trait_value_number": float,
    "trait_value_bool": bool,
    "trait_value_type": str,
}

TRAITS = {
    "is_active": {"type": "boolean"},
    "subscription_level": {
        "type": "string",
        "options": ["basic", "premium", "vip", "enterprise"],
    },
    "days_subscribed": {"type": "number", "options": [10, 20, 30, 40, 50]},
    "created_by": {"type": "string", "options": ["userA", "userB", "userC", "userD"]},
    "email_verified": {"type": "boolean"},
    "login_count": {"type": "number", "options": [1, 5, 10, 15, 20]},
    "user_type": {"type": "string", "options": ["admin", "editor", "viewer", "guest"]},
    "account_balance": {"type": "number", "options": [100, 200, 300, 400, 500]},
    "email": {
        "type": "string",
        "options": [
            "email1@example.com",
            "email2@example.com",
            "email3@example.com",
            "email4@example.com",
        ],
    },
    "age": {"type": "number", "options": [18, 25, 30, 35, 40]},
    "country": {"type": "string", "options": ["USA", "UK", "Canada", "Australia"]},
    "timezone": {"type": "string", "options": ["UTC", "PST", "EST", "CET"]},
    "referral_source": {
        "type": "string",
        "options": ["Facebook", "Google", "Twitter", "LinkedIn"],
    },
    "has_completed_tutorial": {"type": "boolean"},
    "preferred_language": {
        "type": "string",
        "options": ["English", "Spanish", "French", "German"],
    },
    "purchase_count": {"type": "number", "options": [1, 2, 3, 4, 5]},
    "last_login_days_ago": {"type": "number", "options": [1, 7, 14, 30, 60]},
    "average_spent": {"type": "number", "options": [50, 100, 150, 200, 250]},
    "has_newsletter_subscription": {"type": "boolean"},
    "product_category_interest": {
        "type": "string",
        "options": ["Electronics", "Books", "Clothing", "Home"],
    },
    "device_type": {
        "type": "string",
        "options": ["mobile", "desktop", "tablet", "other"],
    },
    "app_version": {"type": "string", "options": ["v1.0", "v1.1", "v1.2", "v2.0"]},
    "customer_segment": {
        "type": "string",
        "options": ["high_value", "low_value", "new_customer", "returning_customer"],
    },
    "feedback_score": {"type": "number", "options": [1, 2, 3, 4, 5]},
    "newsletter_opt_in": {"type": "boolean"},
    "loyalty_points": {"type": "number", "options": [100, 200, 300, 400, 500]},
    "marketing_channel": {
        "type": "string",
        "options": ["Email", "SMS", "Push", "Social Media"],
    },
    "cart_abandonment_count": {"type": "number", "options": [1, 2, 3, 4, 5]},
    "last_purchase_days_ago": {"type": "number", "options": [1, 5, 10, 20, 30]},
    "payment_method": {
        "type": "string",
        "options": ["Credit Card", "PayPal", "Bank Transfer", "Cryptocurrency"],
    },
    "is_invited": {"type": "boolean"},
    "max_friends": {"type": "number", "options": [1, 3, 5, 7]},
    "gender": {"type": "string", "options": ["M", "F", "O"]},
    "q_b_perm": {"type": "number", "options": [3, 5, 6, 10]},
    "extra_hours": {"type": "number", "options": [1, 2]},
    "fav_food": {"type": "string", "options": ["Pops", "Burger", "Chicken", "Salad"]},
    "preferred_contact_method": {
        "type": "string",
        "options": ["Email", "Phone", "SMS", "Push Notification"],
    },
    "purchase_frequency": {"type": "number", "options": [1, 2, 3, 4, 5]},
    "last_payment_method_used": {
        "type": "string",
        "options": ["Credit Card", "PayPal", "Bank Transfer", "Cryptocurrency"],
    },
    "favorite_category": {
        "type": "string",
        "options": ["Electronics", "Books", "Clothing", "Home & Garden"],
    },
    "has_social_media_login": {"type": "boolean"},
    "range_value": {"type": "number", "value": "random"},
    "unique_value": {"type": "string", "value": "unique"},
}

IDENTIFIERS = ["user", "identity", "customer", "client", "account"]


def generate_random_trait_value(trait):
    _uuid = uuid.uuid4()

    if trait["type"] == "boolean":
        return random.choice([True, False])
    elif trait["type"] == "string" and trait.get("value", "") == "unique":
        return str(_uuid)
    elif trait["type"] == "string":
        return random.choice(trait["options"])
    elif trait["type"] == "number" and trait.get("value", "") == "random":
        return float(random.randint(1, 1000))
    elif trait["type"] == "number":
        return float(random.choice(trait["options"]))

    return None


def generate_items_for_trait(trait_key, trait_info):
    global counter
    data = {}
    for _ in range(int(num_items / len(TRAITS.keys()))):
        # Initialize trait value variables
        trait_value_number = None
        trait_value_bool = None

        identity_id = f"{random.choice(IDENTIFIERS)}_{random.randint(100, 9999999)}"
        r = random.randint(1, 10)
        api_key = r if r <= 2 else 1
        trait_value_raw = generate_random_trait_value(trait_info)
        trait_value = str(trait_value_raw)

        trait_value_type = trait_info["type"]
        if trait_value_type == "number":
            trait_value_number = trait_value_raw
        elif trait_value_type == "boolean":
            trait_value_bool = trait_value_raw

        # Calculate the bucket number for the trait_value
        bucket_number = hash(trait_value) % num_buckets

        # Define the partition and bucket paths
        partition_dir = os.path.join(
            output_dir,
            f"environment_api_key=api_key_{api_key}",
            f"trait_name={trait_key}",
        )
        os.makedirs(partition_dir, exist_ok=True)
        parquet_file_path = os.path.join(
            partition_dir, f"bucket_{bucket_number}.parquet"
        )

        # Create a new row
        new_row = {
            "identity_id": identity_id,
            "trait_value": trait_value,
            "trait_value_number": trait_value_number,
            "trait_value_bool": trait_value_bool,
            "trait_value_type": trait_value_type,
        }

        # Append the row to the DataFrame
        if data.get(parquet_file_path) is None:
            data[parquet_file_path] = []
        data[parquet_file_path].append(new_row)

        counter = counter + 1
        if _ % (num_items // 50) == 0:
            print(
                f"Progress: {counter} items processed out of {num_items}. {counter / num_items * 100:.2f}%"
            )

    return data


def write_parquet_files(data):
    for parquet_file in data:
        df = pd.DataFrame(data[parquet_file], columns=expected_columns.keys())
        table = pa.Table.from_pandas(df)
        pq.write_table(table, parquet_file, compression="snappy")


def upload_files_to_s3():
    print(f"Files uploading started at {datetime.datetime.now()}")

    for root, dirs, files in os.walk(output_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            s3_key = os.path.relpath(file_path, output_dir)
            print(f"Uploading {file_path} to s3://{bucket_name}/{s3_prefix}{s3_key}")
            s3_client.upload_file(file_path, bucket_name, f"{s3_prefix}{s3_key}")

    print(f"Files uploading finished at {datetime.datetime.now()}")


def main():
    print(f"Data generation started at {datetime.datetime.now()}")
    for trait_key, trait_info in TRAITS.items():
        print(f"Processing trait: {trait_key}")
        data = generate_items_for_trait(trait_key, trait_info)
        write_parquet_files(data)
    print(f"Data generation completed at {datetime.datetime.now()}")
    upload_files_to_s3()


if __name__ == "__main__":
    main()
