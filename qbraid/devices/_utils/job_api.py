import os
from datetime import datetime

from pymongo import MongoClient, ReturnDocument

from qbraid.devices.enums import JobStatus

from .config_user import get_config


def mongo_init_job(init_data, device_id):
    """Create a new MongoDB job document.

    Returns:
        str: the qbraid_job_id associated with this job

    """
    uri = os.environ["MONGO_DB"]
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    docs = client["test"]["sdk-jobs"]
    init_data["user"] = os.environ["JUPYTERHUB_USER"]
    new_job = docs.insert_one(init_data)
    qbraid_job_id = device_id + ":" + str(new_job.inserted_id)
    docs.update_one({"_id": new_job.inserted_id}, {"$set": {"qbraid_job_id": qbraid_job_id}})
    client.close()
    return qbraid_job_id


def mongo_get_job(qbraid_job_id, update=None):
    """Update a new MongoDB job document.

    Returns:
        dict: the metadata associated with this job

    """
    data = {} if not update else update
    uri = os.environ["MONGO_DB"]
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    docs = client["test"]["sdk-jobs"]
    metadata = docs.find_one_and_update(
        {"qbraid_job_id": qbraid_job_id},
        {"$set": data},
        upsert=False,
        projection={"_id": False},
        return_document=ReturnDocument.AFTER,
    )
    client.close()
    return metadata


def init_job(vendor_job_id, device, circuit, shots):
    data = {
        "qbraid_job_id": None,
        "vendor_job_id": vendor_job_id,
        "qbraid_device_id": device.id,
        "circuit_num_qubits": circuit.num_qubits,
        "circuit_depth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.now(),
        "status": JobStatus.INITIALIZING,
    }
    return mongo_init_job(data, device.id)
