from pymongo import MongoClient, ReturnDocument

import qbraid
from .config_user import get_config


def mongo_init_job(init_data):
    """Create a new MongoDB job document.

    Returns:
        str: the qbraid_job_id associated with this job

    """
    client = MongoClient(qbraid.MONGO_DB, serverSelectionTimeoutMS=5000)
    docs = client["qbraid-sdk"]["jobs"]
    init_data["qbraid_user_id"] = get_config("idToken", "qBraid")  # to be replaced with API call
    new_job = docs.insert_one(init_data)
    qbraid_job_id = str(new_job.inserted_id)
    docs.update_one({"_id": new_job.inserted_id}, {"$set": {"qbraid_job_id": qbraid_job_id}})
    client.close()
    return qbraid_job_id


def mongo_update_job(qbraid_job_id, data):
    """Update a new MongoDB job document.

    Returns:
        dict: the metadata associated with this job

    """
    client = MongoClient(qbraid.MONGO_DB, serverSelectionTimeoutMS=5000)
    docs = client["qbraid-sdk"]["jobs"]
    metadata = docs.find_one_and_update(
        {"qbraid_job_id": qbraid_job_id},
        {"$set": data},
        upsert=False,
        projection={"_id": False},
        return_document=ReturnDocument.AFTER,
    )
    client.close()
    return metadata
