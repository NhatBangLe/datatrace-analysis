import boto3
import logging
from botocore.exceptions import ClientError
from src.config import settings
from src.services import IStorageService

logger = logging.getLogger("S3StorageService")


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
        
        # Ensure the default bucket exists
        try:
            self._s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            logger.debug(f"Bucket {settings.S3_BUCKET_NAME} exists.")
        except ClientError:
            logger.info(f"Bucket {settings.S3_BUCKET_NAME} does not exist. Creating it...")
            try:
                self._s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                logger.info(f"Successfully created bucket {settings.S3_BUCKET_NAME}.")
            except ClientError as e:
                logger.error(f"Failed to create bucket {settings.S3_BUCKET_NAME}: {e}")

        logger.info(
            f"S3StorageService initialized for endpoint: {settings.SEAWEEDFS_ENDPOINT_URL}"
        )

    def upload_file(
        self,
        file_content,
        filename,
        **kwargs,
    ):
        """
        Uploads a file to the specified S3 bucket.
        Returns the S3 key (filename) if successful, raises an exception otherwise.
        """
        bucket_name = str(kwargs.get("bucket_name") or settings.S3_BUCKET_NAME)
        mime_type = str(kwargs.get("mime_type") or "application/octet-stream")
        folder = str(kwargs.get("folder")) if kwargs.get("folder") else None
        s3_key = f"{f'{folder}/' if folder else ''}{filename}"

        try:
            extra_args = {}
            if "content_length" in kwargs:
                extra_args["ContentLength"] = kwargs["content_length"]

            self._s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=mime_type,
                **extra_args,
            )
            logger.debug(f"Successfully uploaded {s3_key} to bucket {bucket_name}")
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload {s3_key} to S3 bucket {bucket_name}: {e}")
            raise RuntimeError
