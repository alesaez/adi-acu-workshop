import base64
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import BlobContainer, StorageAccountCreateParameters, StorageAccountPropertiesCreateParameters
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


CONTAINER_NAME = "documents"
STORAGE_BLOB_DATA_CONTRIBUTOR = "Storage Blob Data Contributor"
STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
STORAGE_ACCOUNT_NAME_PATTERN = re.compile(r"^[a-z0-9]{3,24}$")


def optional_setting(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    return "" if not value or value.startswith("<") else value


def require_setting(name: str) -> str:
    value = optional_setting(name)
    if not value:
        raise ValueError(f"Set {name} in workshop/.env")
    return value


def validate_storage_account_name(account_name: str) -> str:
    if not STORAGE_ACCOUNT_NAME_PATTERN.fullmatch(account_name):
        raise ValueError(
            "STORAGE_ACCOUNT_NAME must be 3 to 24 characters and contain only lowercase letters and numbers."
        )
    return account_name


def get_storage_account_name() -> str:
    configured_name = optional_setting("STORAGE_ACCOUNT_NAME")
    if configured_name:
        return validate_storage_account_name(configured_name)
    return f"aidocs{random.randint(1, 999999):08d}"


def save_env_setting(env_path: Path, name: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    setting = f"{name}={value}"

    for index, line in enumerate(lines):
        if line.startswith(f"{name}="):
            lines[index] = setting
            break
    else:
        if lines and lines[-1]:
            lines.append("")
        lines.append(setting)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_current_subscription_id(credential: DefaultAzureCredential) -> str:
    try:
        token = credential.get_token("https://management.azure.com/.default").token
        request = urllib.request.Request(
            "https://management.azure.com/subscriptions?api-version=2022-12-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(request) as response:
            subscriptions = json.loads(response.read().decode("utf-8")).get("value", [])
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(
            "Set STORAGE_SUBSCRIPTION_ID in workshop/.env, or sign in with an Azure identity that can list subscriptions. "
            f"Azure error: {exc.code} {exc.reason}. {error_body}"
        ) from exc
    except Exception as exc:
        raise ValueError(
            "Set STORAGE_SUBSCRIPTION_ID in workshop/.env, or sign in with an Azure identity that can list subscriptions."
        ) from exc

    enabled_subscriptions = [
        subscription
        for subscription in subscriptions
        if str(subscription.get("state", "")).lower() == "enabled"
    ]
    subscriptions = enabled_subscriptions or subscriptions

    if len(subscriptions) == 1:
        subscription_id = (subscriptions[0].get("subscriptionId") or "").strip()
        if subscription_id:
            return subscription_id

    if not subscriptions:
        raise ValueError("Set STORAGE_SUBSCRIPTION_ID in workshop/.env. No Azure subscriptions were found for the current credential.")

    available_subscriptions = "\n".join(
        f"- {subscription.get('displayName', '<unnamed>')}: {subscription.get('subscriptionId', '<missing-id>')}"
        for subscription in subscriptions
    )
    raise ValueError(
        "Multiple Azure subscriptions were found. Set STORAGE_SUBSCRIPTION_ID in workshop/.env to one of these values:\n"
        f"{available_subscriptions}"
    )


def get_current_principal_id(credential: DefaultAzureCredential) -> str:
    token = credential.get_token("https://management.azure.com/.default").token
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")))

    principal_id = (claims.get("oid") or "").strip()
    if not principal_id:
        raise ValueError("Could not determine the current Azure principal object ID from the access token.")
    return principal_id


def grant_current_user_blob_data_contributor(
    authorization_client: AuthorizationManagementClient,
    credential: DefaultAzureCredential,
    storage_account_scope: str,
) -> None:
    principal_id = get_current_principal_id(credential)
    role_definition_id = f"{storage_account_scope}/providers/Microsoft.Authorization/roleDefinitions/{STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID}"
    role_assignment_name = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{storage_account_scope}/{principal_id}/{STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID}"))

    print(f"Granting current user {STORAGE_BLOB_DATA_CONTRIBUTOR} on the storage account...")
    try:
        authorization_client.role_assignments.create(
            storage_account_scope,
            role_assignment_name,
            RoleAssignmentCreateParameters(
                role_definition_id=role_definition_id,
                principal_id=principal_id,
                principal_type="User",
            ),
        )
    except HttpResponseError as exc:
        if exc.error and exc.error.code == "RoleAssignmentExists":
            return
        raise ValueError(
            f"Could not assign {STORAGE_BLOB_DATA_CONTRIBUTOR}. "
            "Your account must have Owner or User Access Administrator permission on the storage account. "
            f"Azure error: {exc.message}"
        ) from exc


def get_or_create_storage_account(
    storage_client: StorageManagementClient,
    resource_group: str,
    account_name: str,
    location: str,
):
    try:
        storage_account = storage_client.storage_accounts.get_properties(resource_group, account_name)
        print(f"Using existing storage account: {account_name}")
        return storage_account
    except ResourceNotFoundError:
        pass

    print(f"Creating storage account: {account_name}")
    poller = storage_client.storage_accounts.begin_create(
        resource_group,
        account_name,
        StorageAccountCreateParameters(
            sku={"name": "Standard_LRS"},
            kind="StorageV2",
            location=location,
            properties=StorageAccountPropertiesCreateParameters(
                allow_blob_public_access=False,
                enable_https_traffic_only=True,
                minimum_tls_version="TLS1_2",
            ),
        ),
    )
    return poller.result()


def get_public_network_access(storage_account) -> str:
    value = getattr(storage_account, "public_network_access", "")
    return getattr(value, "value", str(value)).lower()


def ensure_blob_container(storage_client: StorageManagementClient, resource_group: str, account_name: str) -> None:
    try:
        storage_client.blob_containers.get(resource_group, account_name, CONTAINER_NAME)
        print(f"Using existing blob container: {CONTAINER_NAME}")
    except ResourceNotFoundError:
        print(f"Creating blob container: {CONTAINER_NAME}")
        storage_client.blob_containers.create(
            resource_group,
            account_name,
            CONTAINER_NAME,
            BlobContainer(public_access="None"),
        )


def extract_documents(zip_path: Path, documents_dir: Path) -> None:
    if documents_dir.exists() and any(documents_dir.glob("*.pdf")):
        return

    if not zip_path.exists():
        raise FileNotFoundError(f"Documents zip file not found: {zip_path}")

    print(f"Extracting {zip_path.name} to {documents_dir}...")
    documents_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(documents_dir)


def upload_documents(blob_service_client: BlobServiceClient, documents_dir: Path) -> None:
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    pdf_files = sorted(documents_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF documents found in {documents_dir}")

    for file_path in pdf_files:
        with file_path.open("rb") as data:
            container_client.upload_blob(name=file_path.name, data=data, overwrite=True)
        print(f"Uploaded: {file_path.name}")


def upload_documents_with_rbac_retry(blob_service_client: BlobServiceClient, documents_dir: Path) -> None:
    retryable_error_codes = {"AuthorizationFailure", "AuthorizationPermissionMismatch"}

    for attempt in range(1, 7):
        try:
            upload_documents(blob_service_client, documents_dir)
            return
        except HttpResponseError as exc:
            if exc.error_code not in retryable_error_codes or attempt == 6:
                raise
            wait_seconds = attempt * 10
            print(f"Waiting {wait_seconds} seconds for role assignment propagation before retrying upload...")
            time.sleep(wait_seconds)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    workshop_dir = script_dir.parent
    env_path = workshop_dir / ".env"
    zip_path = script_dir / "documents.zip"
    documents_dir = script_dir / "documents"

    load_dotenv(env_path)

    credential = DefaultAzureCredential()

    subscription_id = optional_setting("STORAGE_SUBSCRIPTION_ID") or optional_setting("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        subscription_id = get_current_subscription_id(credential)

    resource_group = require_setting("STORAGE_RESOURCE_GROUP")
    location = os.getenv("STORAGE_LOCATION", "eastus2")

    storage_client = StorageManagementClient(credential, subscription_id)
    authorization_client = AuthorizationManagementClient(credential, subscription_id)

    configured_account_name = optional_setting("STORAGE_ACCOUNT_NAME")
    account_name = validate_storage_account_name(configured_account_name) if configured_account_name else get_storage_account_name()

    print(f"Using subscription: {subscription_id}")
    print(f"Storage resource group: {resource_group}")
    print(f"Storage location: {location}")

    extract_documents(zip_path, documents_dir)
    storage_account = get_or_create_storage_account(storage_client, resource_group, account_name, location)
    if not configured_account_name:
        save_env_setting(env_path, "STORAGE_ACCOUNT_NAME", account_name)
        print(f"Saved STORAGE_ACCOUNT_NAME={account_name} to {env_path}")

    ensure_blob_container(storage_client, resource_group, account_name)

    if get_public_network_access(storage_account) == "disabled":
        raise ValueError(
            f"The {CONTAINER_NAME} container was created, but local document upload cannot continue because "
            f"storage account {account_name} has public network access disabled. Enable public network access for this lab, "
            "or clear STORAGE_ACCOUNT_NAME in workshop/.env so the script can create a new lab storage account."
        )

    grant_current_user_blob_data_contributor(authorization_client, credential, storage_account.id)

    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

    print("Uploading documents...")
    upload_documents_with_rbac_retry(blob_service_client, documents_dir)

    container_url = f"{account_url}/{CONTAINER_NAME}"

    print("-------------------------------------")
    print(f"Storage account: {account_name}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Container URL: {container_url}")
    print("Use this storage account and container when importing data into Azure AI Search.")


if __name__ == "__main__":
    main()
