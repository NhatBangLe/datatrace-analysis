import boto3
import logging
from botocore.exceptions import ClientError
from src.config import settings
from src.services import IStorageService

logger = logging.getLogger(__name__)


class S3StorageService(IStorageService):
    """
    Service to interact with SeaweedFS S3 Gateway using boto3.
    """

    def __init__(self):
        self._s3_client = boto3.client(
            "s3",
            endpoint_url=settings.SEAWEEDFS_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )
        logger.info(
            f"S3StorageService initialized for endpoint: {settings.SEAWEEDFS_ENDPOINT_URL}"
        )

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        **kwargs,
    ) -> str:
        """
        Uploads a file to the specified S3 bucket.
        Returns the S3 key (filename) if successful, raises an exception otherwise.
        """
        bucket_name = str(kwargs.get("bucket_name") or settings.S3_BUCKET_NAME)

        try:
            self._s3_client.put_object(
                Bucket=bucket_name, Key=filename, Body=file_content
            )
            logger.info(f"Successfully uploaded {filename} to bucket {bucket_name}")
            return filename
        except ClientError as e:
            logger.error(f"Failed to upload {filename} to S3 bucket {bucket_name}: {e}")
            raise
