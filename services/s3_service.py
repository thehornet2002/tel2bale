import os
import re
import uuid
import aioboto3
from botocore.exceptions import ClientError
from utils.logger import get_logger

logger = get_logger(__name__)


async def create_connection(access_key: str, secret_key: str) -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


async def empty_bucket(s3_client, bucket_name: str):
    """Purge all objects in bucket in batches of 1000."""
    logger.warning(f"[S3] Emptying all objects in bucket '{bucket_name}'...")
    try:
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
    except Exception as e:
        logger.error(f"[S3] Failed to empty bucket: {e}")
        raise e


async def upload_file(
    session: aioboto3.Session,
    file_path: str,
    endpoint_url: str,
    object_key: str,
    bucket_name: str = "my-telegram-bot",
    content_type: str = "application/octet-stream",
    expires_in: int = 3600,
) -> str:
    """
    Upload file to S3 storage:
    1. Ensure bucket exists.
    2. Rename file to UUID with safe extension to prevent collisions and path traversal.
    3. Stream upload with auto-recovery on bucket quota exceeded.
    4. Generate expiring presigned URL.
    5. Clean up local disk file.
    """
    try:
        if not os.path.exists(file_path):
            return "❌ فایل برای آپلود یافت نشد."

        file_size = os.path.getsize(file_path)
        _, ext = os.path.splitext(file_path)
        safe_ext = re.sub(r"[^a-zA-Z0-9_\.]", "", ext)[:10]
        unique_object_key = f"{uuid.uuid4().hex}{safe_ext}"

        async with session.client("s3", endpoint_url=endpoint_url) as s3:
            # Step 1: Ensure bucket exists
            try:
                await s3.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ('404', 'NoSuchBucket'):
                    logger.info(f"[S3] Bucket '{bucket_name}' does not exist. Creating...")
                    await s3.create_bucket(Bucket=bucket_name)
                else:
                    raise e

            # Step 2: Upload file with retry on quota exceeded
            with open(file_path, "rb") as file_data:
                try:
                    await s3.put_object(
                        Bucket=bucket_name,
                        Key=unique_object_key,
                        Body=file_data,
                        ContentType=content_type
                    )
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code in ["QuotaExceeded", "InsufficientStorage", "RequestLimitExceeded", "403"]:
                        logger.warning(f"[S3] Bucket storage exceeded ({error_code}). Purging bucket...")
                        await empty_bucket(s3, bucket_name)
                        file_data.seek(0)
                        logger.info("[S3] Retrying upload after bucket purge...")
                        await s3.put_object(
                            Bucket=bucket_name,
                            Key=unique_object_key,
                            Body=file_data,
                            ContentType=content_type
                        )
                    else:
                        raise e

            # Step 3: Generate presigned URL
            file_url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': unique_object_key},
                ExpiresIn=expires_in
            )

            logger.info(f"[S3] Successful upload: {unique_object_key} ({file_size / 1024 / 1024:.2f} MB)")
            return file_url

    except ClientError as e:
        logger.error(f"[S3] ClientError during upload: {e}")
        return "❌ خطای دسترسی یا اتصال به باکت S3 آروان."
    except Exception as e:
        logger.error(f"[S3] Unexpected error during upload: {e}")
        return "❌ خطا در آپلود فایل روی فضای ابری."
    finally:
        # Step 4: Always clean up local temporary file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[S3] Cleaned up temporary file: {file_path}")
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
