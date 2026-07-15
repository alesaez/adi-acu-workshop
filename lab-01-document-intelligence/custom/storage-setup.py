import base64
import json
import os
import random
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, StorageAccountPropertiesCreateParameters
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


CONTAINER_NAME = "sampleforms"
STORAGE_BLOB_DATA_CONTRIBUTOR = "Storage Blob Data Contributor"
STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
STORAGE_ACCOUNT_NAME_PATTERN = re.compile(r"^[a-z0-9]{3,24}$")
COGNITIVE_SERVICES_API_VERSION = "2023-05-01"


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
    return f"aiforms{random.randint(1, 99999):08d}"


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


def get_doc_intelligence_account_name() -> str:
    configured_name = optional_setting("DOC_INTELLIGENCE_RESOURCE_NAME")
    if configured_name:
        return configured_name

    endpoint = require_setting("DOC_INTELLIGENCE_ENDPOINT")
    host = urllib.parse.urlparse(endpoint).hostname or ""
    account_name = host.split(".", 1)[0]
    if not account_name:
        raise ValueError("Set DOC_INTELLIGENCE_RESOURCE_NAME in workshop/.env, or use a standard Document Intelligence endpoint.")
    return account_name


def arm_request(credential: DefaultAzureCredential, method: str, url: str, body: dict | None = None) -> dict:
    token = credential.get_token("https://management.azure.com/.default").token
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Azure management request failed: {exc.code} {exc.reason}. {error_body}") from exc

    return json.loads(response_body) if response_body else {}


def get_current_subscription_id() -> str:
    try:
        result = subprocess.run(
            ["az", "account", "show", "--output", "json"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ValueError("Set STORAGE_SUBSCRIPTION_ID in workshop/.env, or install Azure CLI and run az login.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip()
        raise ValueError(f"Set STORAGE_SUBSCRIPTION_ID in workshop/.env, or run az login. Azure CLI error: {message}") from exc

    account = json.loads(result.stdout)
    subscription_id = (account.get("id") or "").strip()
    if not subscription_id:
        raise ValueError("Set STORAGE_SUBSCRIPTION_ID in workshop/.env, or select a default subscription with az account set.")
    return subscription_id


def get_current_principal_id(credential: DefaultAzureCredential) -> str:
    token = credential.get_token("https://management.azure.com/.default").token
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")))

    principal_id = (claims.get("oid") or "").strip()
    if not principal_id:
        raise ValueError("Could not determine the current Azure principal object ID from the access token.")
    return principal_id


def grant_blob_data_contributor_to_principal(
    authorization_client: AuthorizationManagementClient,
    storage_account_scope: str,
    principal_id: str,
    principal_type: str,
    display_name: str,
) -> None:
    role_definition_id = f"{storage_account_scope}/providers/Microsoft.Authorization/roleDefinitions/{STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID}"
    role_assignment_name = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{storage_account_scope}/{principal_id}/{STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID}"))

    print(f"Granting {display_name} {STORAGE_BLOB_DATA_CONTRIBUTOR} on the storage account...")
    try:
        authorization_client.role_assignments.create(
            storage_account_scope,
            role_assignment_name,
            RoleAssignmentCreateParameters(
                role_definition_id=role_definition_id,
                principal_id=principal_id,
                principal_type=principal_type,
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


def grant_current_user_blob_data_contributor(
    authorization_client: AuthorizationManagementClient,
    credential: DefaultAzureCredential,
    storage_account_scope: str,
) -> None:
    grant_blob_data_contributor_to_principal(
        authorization_client,
        storage_account_scope,
        get_current_principal_id(credential),
        "User",
        "current user",
    )


def get_doc_intelligence_managed_identity_principal_id(
    credential: DefaultAzureCredential,
    subscription_id: str,
    resource_group: str,
) -> str:
    account_name = get_doc_intelligence_account_name()
    resource_id = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{account_name}"
    )
    url = f"https://management.azure.com{resource_id}?api-version={COGNITIVE_SERVICES_API_VERSION}"
    account = arm_request(credential, "GET", url)

    identity = account.get("identity") or {}
    principal_id = (identity.get("principalId") or "").strip()
    if principal_id:
        return principal_id

    print(f"Enabling system-assigned managed identity on Document Intelligence resource: {account_name}")
    account = arm_request(credential, "PATCH", url, {"identity": {"type": "SystemAssigned"}})
    principal_id = ((account.get("identity") or {}).get("principalId") or "").strip()
    if not principal_id:
        raise ValueError(
            "Could not enable or read the Document Intelligence managed identity. "
            "Your account must have permission to update the Document Intelligence resource."
        )
    return principal_id


def upload_sample_forms(blob_service_client: BlobServiceClient, sample_forms_dir: Path) -> None:
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    try:
        container_client.create_container()
    except ResourceExistsError:
        pass

    for file_path in sample_forms_dir.rglob("*"):
        if not file_path.is_file():
            continue

        blob_name = file_path.relative_to(sample_forms_dir).as_posix()
        with file_path.open("rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)


def upload_sample_forms_with_rbac_retry(blob_service_client: BlobServiceClient, sample_forms_dir: Path) -> None:
    for attempt in range(1, 7):
        try:
            upload_sample_forms(blob_service_client, sample_forms_dir)
            return
        except HttpResponseError as exc:
            if exc.error_code != "AuthorizationPermissionMismatch" or attempt == 6:
                raise
            wait_seconds = attempt * 10
            print(f"Waiting {wait_seconds} seconds for role assignment propagation before retrying upload...")
            time.sleep(wait_seconds)


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
                allow_shared_key_access=False,
                enable_https_traffic_only=True,
                minimum_tls_version="TLS1_2",
            ),
        ),
    )
    return poller.result()


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    workshop_dir = script_dir.parents[1]
    env_path = workshop_dir / ".env"
    sample_forms_dir = script_dir / "sample-forms"

    load_dotenv(env_path)

    subscription_id = optional_setting("STORAGE_SUBSCRIPTION_ID") or optional_setting("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        subscription_id = get_current_subscription_id()

    resource_group = require_setting("STORAGE_RESOURCE_GROUP")
    doc_intelligence_resource_group = optional_setting("DOC_INTELLIGENCE_RESOURCE_GROUP") or resource_group
    location = os.getenv("STORAGE_LOCATION", "eastus2")

    if not sample_forms_dir.exists():
        raise FileNotFoundError(f"Sample forms folder not found: {sample_forms_dir}")

    credential = DefaultAzureCredential()
    storage_client = StorageManagementClient(credential, subscription_id)
    authorization_client = AuthorizationManagementClient(credential, subscription_id)

    configured_account_name = optional_setting("STORAGE_ACCOUNT_NAME")
    account_name = validate_storage_account_name(configured_account_name) if configured_account_name else get_storage_account_name()

    print(f"Using subscription: {subscription_id}")
    storage_account = get_or_create_storage_account(storage_client, resource_group, account_name, location)
    if not configured_account_name:
        save_env_setting(env_path, "STORAGE_ACCOUNT_NAME", account_name)
        print(f"Saved STORAGE_ACCOUNT_NAME={account_name} to {env_path}")
    grant_current_user_blob_data_contributor(authorization_client, credential, storage_account.id)
    doc_intelligence_principal_id = get_doc_intelligence_managed_identity_principal_id(
        credential,
        subscription_id,
        doc_intelligence_resource_group,
    )
    grant_blob_data_contributor_to_principal(
        authorization_client,
        storage_account.id,
        doc_intelligence_principal_id,
        "ServicePrincipal",
        "Document Intelligence managed identity",
    )

    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

    print("Uploading sample forms...")
    upload_sample_forms_with_rbac_retry(blob_service_client, sample_forms_dir)

    container_url = f"{account_url}/{CONTAINER_NAME}"

    print("-------------------------------------")
    print(f"Storage account: {account_name}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Container URL: {container_url}")
    print("Use the same signed-in Azure account in Document Intelligence Studio to connect to this storage container.")


if __name__ == "__main__":
    main()