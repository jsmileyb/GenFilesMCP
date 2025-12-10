from io import BytesIO
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger("GenFilesMCP")

try:
    from azure.storage.blob import (
        BlobServiceClient,
        BlobSasPermissions,
        generate_blob_sas,
        ContentSettings,
    )
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import AzureError

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning(
        "Azure SDK not available. Install azure-storage-blob and azure-identity to enable Azure Blob Storage support."
    )


def get_azure_blob_client(
    connection_string: str = None,
    account_name: str = None,
    use_managed_identity: bool = False,
) -> BlobServiceClient:
    """
    Get Azure Blob Service Client using either connection string or managed identity.

    Args:
        connection_string (str, optional): Azure Storage connection string
        account_name (str, optional): Azure Storage account name (for managed identity)
        use_managed_identity (bool): Whether to use Azure managed identity for authentication

    Returns:
        BlobServiceClient: Authenticated blob service client

    Raises:
        ValueError: If neither connection string nor account name is provided
        ImportError: If Azure SDK is not available
    """
    if not AZURE_AVAILABLE:
        raise ImportError(
            "Azure SDK is not installed. Please install azure-storage-blob and azure-identity."
        )

    try:
        if use_managed_identity:
            if not account_name:
                raise ValueError(
                    "Account name is required when using managed identity authentication."
                )
            credential = DefaultAzureCredential()
            account_url = f"https://{account_name}.blob.core.windows.net"
            blob_service_client = BlobServiceClient(
                account_url=account_url, credential=credential
            )
            logger.info(
                f"Connected to Azure Blob Storage using managed identity: {account_name}"
            )
        else:
            if not connection_string:
                raise ValueError(
                    "Connection string is required when not using managed identity authentication."
                )
            blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
            logger.info("Connected to Azure Blob Storage using connection string")

        return blob_service_client

    except AzureError as e:
        logger.error(f"Azure authentication error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating Azure Blob Service Client: {str(e)}")
        raise


def upload_to_azure_blob(
    blob_service_client: BlobServiceClient,
    container_name: str,
    file_data: BytesIO,
    blob_name: str,
    content_type: str = "application/octet-stream",
) -> bool:
    """
    Upload a file to Azure Blob Storage.

    Args:
        blob_service_client (BlobServiceClient): Authenticated blob service client
        container_name (str): Name of the blob container
        file_data (BytesIO): File data to upload
        blob_name (str): Name for the blob in Azure Storage
        content_type (str): MIME type of the file

    Returns:
        bool: True if upload successful, False otherwise
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure SDK is not available")
        return False

    try:
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)

        # Create container if it doesn't exist
        try:
            container_client.create_container()
            logger.info(f"Created container: {container_name}")
        except Exception as e:
            # Container already exists or we don't have permission to create
            logger.debug(f"Container check: {str(e)}")

        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)

        # Reset file pointer to beginning
        file_data.seek(0)

        # Upload the file with content settings
        content_settings = ContentSettings(content_type=content_type)
        blob_client.upload_blob(
            file_data, overwrite=True, content_settings=content_settings
        )

        logger.info(f"Successfully uploaded {blob_name} to Azure Blob Storage")
        return True

    except AzureError as e:
        logger.error(f"Azure upload error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error uploading to Azure Blob Storage: {str(e)}")
        return False


def generate_sas_url(
    blob_service_client: BlobServiceClient,
    container_name: str,
    blob_name: str,
    expiry_hours: int = 24,
    account_name: str = None,
    account_key: str = None,
) -> str:
    """
    Generate a SAS URL for a blob with read permissions.

    Args:
        blob_service_client (BlobServiceClient): Authenticated blob service client
        container_name (str): Name of the blob container
        blob_name (str): Name of the blob
        expiry_hours (int): Hours until the SAS URL expires (default: 24)
        account_name (str, optional): Storage account name (required for SAS generation)
        account_key (str, optional): Storage account key (required for SAS generation)

    Returns:
        str: SAS URL for the blob, or empty string if generation fails
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure SDK is not available")
        return ""

    try:
        # If we don't have account key, try to extract it from the connection string
        if not account_key and hasattr(blob_service_client, "credential"):
            # For connection string authentication, extract account key
            if hasattr(blob_service_client.credential, "account_key"):
                account_key = blob_service_client.credential.account_key

        if not account_name or not account_key:
            logger.error("Account name and key are required for SAS URL generation")
            # Return the direct blob URL without SAS (will require authentication)
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            return blob_client.url

        # Calculate expiry time
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)

        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
        )

        # Construct full SAS URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

        logger.info(
            f"Generated SAS URL for {blob_name}, expires in {expiry_hours} hours"
        )
        return blob_url

    except Exception as e:
        logger.error(f"Error generating SAS URL: {str(e)}")
        # Fallback: return direct blob URL
        try:
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            return blob_client.url
        except:
            return ""


def extract_account_info_from_connection_string(connection_string: str) -> tuple:
    """
    Extract account name and account key from Azure Storage connection string.

    Args:
        connection_string (str): Azure Storage connection string

    Returns:
        tuple: (account_name, account_key)
    """
    try:
        parts = connection_string.split(";")
        account_name = None
        account_key = None

        for part in parts:
            if part.startswith("AccountName="):
                account_name = part.split("=", 1)[1]
            elif part.startswith("AccountKey="):
                account_key = part.split("=", 1)[1]

        return account_name, account_key
    except Exception as e:
        logger.error(f"Error parsing connection string: {str(e)}")
        return None, None
