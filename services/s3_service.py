import os
import re
import uuid
import aioboto3
from botocore.exceptions import ClientError
from utils.logger import get_logger

logger = get_logger(__name__)


class S3StorageQuotaExceeded(Exception):
    """Raised when S3 storage bucket quota or capacity limit is reached."""
    pass


async def create_connection(access_key: str, secret_key: str) -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


async def empty_bucket(session: aioboto3.Session, endpoint_url: str, bucket_name: str = "my-telegram-bot"):
    """Purge objects in bucket upon explicit user authorization."""
    logger.warning(f"[S3] Explicitly emptying objects in bucket '{bucket_name}'...")
    try:
        async with session.client("s3", endpoint_url=endpoint_url) as s3_client:
            paginator = s3_client.get_paginator('list_objects_v2')
            async for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    if objects_to_delete:
                        await s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
        logger.info(f"[S3] Bucket '{bucket_name}' successfully emptied.")
        return True
    except Exception as e:
        logger.error(f"[S3] Failed to empty bucket: {e}")
        return False


async def upload_file(
    session: aioboto3.Session,
    file_path: str,
    endpoint_url: str,
    user_id: int | None = None,
    bucket_name: str = "my-telegram-bot",
    content_type: str = "application/octet-stream",
    expires_in: int = 3600,
) -> str:
    """
    Upload file to S3 storage with user-isolated prefix:
    1. Ensure bucket exists.
    2. Store under users/{user_id}/{uuid}.{ext}.
    3. Stream upload using Chunked IO / file object.
    4. Never delete bucket content automatically.
    5. Clean up local disk file.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError("فایل برای آپلود یافت نشد.")

        file_size = os.path.getsize(file_path)
        _, ext = os.path.splitext(file_path)
        safe_ext = re.sub(r"[^a-zA-Z0-9_\.]", "", ext)[:10].lower()
        unique_name = f"{uuid.uuid4().hex}{safe_ext}"
        
        # User-isolated object key hierarchy
        if user_id:
            object_key = f"users/{user_id}/{unique_name}"
        else:
            object_key = f"uploads/{unique_name}"

        async with session.client("s3", endpoint_url=endpoint_url) as s3:
            try:
                await s3.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ('404', 'NoSuchBucket'):
                    logger.info(f"[S3] Bucket '{bucket_name}' does not exist. Creating...")
                    await s3.create_bucket(Bucket=bucket_name)
                else:
                    raise e

            with open(file_path, "rb") as file_data:
                try:
                    await s3.put_object(
                        Bucket=bucket_name,
                        Key=object_key,
                        Body=file_data,
                        ContentType=content_type
                    )
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code in ["QuotaExceeded", "InsufficientStorage", "RequestLimitExceeded"]:
                        logger.warning(f"[S3] Storage quota exceeded ({error_code}) for user {user_id}")
                        raise S3StorageQuotaExceeded("فضای باکت S3 شما تکمیل شده است.")
                    raise e

            file_url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )

            logger.info(f"[S3] Uploaded: {object_key} ({file_size / 1024 / 1024:.2f} MB)")
            return file_url

    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"[S3] Failed to remove temporary file {file_path}: {e}")


async def verify_credentials(access_key: str, secret_key: str, endpoint_url: str) -> bool:
    """Validate S3 credentials and endpoint accessibility."""
    try:
        session = await create_connection(access_key, secret_key)
        async with session.client("s3", endpoint_url=endpoint_url) as s3:
            await s3.list_buckets()
        return True
    except Exception as e:
        logger.warning(f"[S3] Credential verification failed: {e}")
        return False
