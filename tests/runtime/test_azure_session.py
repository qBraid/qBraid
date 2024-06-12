from qbraid.runtime.azure.provider import AzureSession, AzureQuantumProvider
import time

az_sesh = AzureSession(client_id=client_id, client_secret=client_secret, tenant_id=tenant_id,
                       location_name=location_name, subscription_id=subscription_id, resource_group_name=resource_group,
                       workspace_name=workspace_name, storage_account=storage_account, connection_string=connection_string)

devices = az_sesh.get_devices()
my_device = az_sesh.get_device("microsoft.estimator")
my_job = az_sesh.create_job("job-data-tests", "Emulator", 2)

for key, value in az_sesh.jobs.items():
    job_id = key
    break

print("The actual job id is: ", job_id)
print(az_sesh.jobs)

print("My job is ", az_sesh.get_job(job_id))