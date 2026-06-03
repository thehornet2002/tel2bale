import aioboto3
from botocore.exceptions import ClientError
import os
import uuid  # <--- اضافه شدن کتابخانه uuid
from utils.logger import get_logger

logger = get_logger(__name__)



async def create_connection(access_key: str, secret_key: str) -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


async def empty_bucket(s3_client, bucket_name: str):
    """
    تابع کمکی برای حذف تمام فایل‌های یک باکت.
    برای سرعت بالاتر، فایل‌ها را در دسته‌های 1000 تایی (محدودیت S3) پاک می‌کند.
    """
    logger.warning(f"[ARVAN] در حال حذف تمامی فایل‌های باکت '{bucket_name}'...")
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        async for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                # استخراج کلید (نام) فایل‌ها برای حذف
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                
                if objects_to_delete:
                    await s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
        logger.info(f"[ARVAN] باکت '{bucket_name}' با موفقیت تخلیه شد.")
    except Exception as e:
        logger.error(f"[ARVAN] خطا در تخلیه باکت: {e}")
        raise e


async def upload_file(
    session: aioboto3.Session,
    file_path: str,
    endpoint_url: str ,
    object_key: str,
    bucket_name: str = "my-telegram-bot",
    content_type: str = "application/octet-stream",
    expires_in: int = 3600,
) -> str:
    """
    ۱. بررسی و ساخت باکت در صورت عدم وجود
    ۲. تغییر نام فایل به UUID جهت جلوگیری از تداخل
    ۳. آپلود استریمی (کمترین درگیری رم)
    ۴. هندل کردن پر بودن باکت (خالی کردن و تلاش مجدد)
    ۵. حذف خودکار فایل از حافظه سرور پس از اتمام کار
    """
    try:
        if not os.path.exists(file_path):
            return "❌ فایل برای آپلود یافت نشد."

        # محاسبه حجم برای لاگ
        file_size = os.path.getsize(file_path)
        
        # --- تولید نام یکتا (UUID) با حفظ پسوند فایل ---
        _, ext = os.path.splitext(file_path)  # استخراج پسوند فایل دانلودی
        unique_object_key = f"{uuid.uuid4().hex}{ext}"  # مثال: 5f9a3b...8e.jpg
        
        async with session.client("s3", endpoint_url=endpoint_url) as s3:
            
            # --- مرحله اول: بررسی وجود یا ساخت باکت ---
            try:
                await s3.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404' or error_code == 'NoSuchBucket':
                    logger.info(f"[ARVAN] باکت '{bucket_name}' وجود ندارد. در حال ساخت...")
                    await s3.create_bucket(Bucket=bucket_name)
                else:
                    raise e

            # --- مرحله دوم: آپلود با استراتژی تلاش مجدد در صورت پر بودن ---
            with open(file_path, "rb") as file_data:
                try:
                    await s3.put_object(
                        Bucket=bucket_name,
                        Key=unique_object_key,  # استفاده از نام یکتای تولید شده
                        Body=file_data,
                        ContentType=content_type
                    )
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    if error_code in ["QuotaExceeded", "InsufficientStorage", "RequestLimitExceeded", "403"]:
                        logger.warning(f"[ARVAN] باکت پر شده است (خطای {error_code}). شروع فرآیند پاکسازی...")
                        await empty_bucket(s3, bucket_name)
                        file_data.seek(0)
                        
                        logger.info("[ARVAN] تلاش مجدد برای آپلود فایل پس از تخلیه باکت...")
                        await s3.put_object(
                            Bucket=bucket_name,
                            Key=unique_object_key, # استفاده از نام یکتا
                            Body=file_data,
                            ContentType=content_type
                        )
                    else:
                        raise e

            # --- مرحله سوم: تولید لینک موقت ---
            file_url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': unique_object_key}, # استفاده از نام یکتا
                ExpiresIn=expires_in
            )
            
            logger.info(f"[ARVAN] آپلود موفق: {unique_object_key} ({file_size / 1024 / 1024:.2f} MB)")
            return file_url

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return f"❌ خطای S3: {error_msg}"
    except Exception as e:
        return f"❌ خطای غیرمنتظره: {e}"
    
    finally:
        # --- مرحله چهارم: حذف حتمی فایل از روی دیسک (در هر شرایطی) ---
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleanup: Temporary file {file_path} removed.")
            except Exception as cleanup_error:
                logger.error(f"Cleanup Error: {cleanup_error}")

async def verify_credentials(access_key: str, secret_key: str, endpoint_url: str ) -> bool:
    """
    بررسی صحت access_key و secret_key با ارسال یک درخواست سبک به آروان.

    از list_buckets استفاده می‌کنیم چون:
      - هیچ bucket name نیاز نداره
      - کمترین permission رو می‌خواد
      - تنها هدفش اثبات credentials هستش

    Returns:
        True  → credentials معتبر هستند
        False → credentials نامعتبر یا خطا در اتصال
    """
    try:
        session = await create_connection(access_key, secret_key)
        async with session.client("s3", endpoint_url=endpoint_url) as s3:
            await s3.list_buckets()
        logger.info("[ARVAN] Credential verification successful.")
        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        logger.warning(f"[ARVAN] Credential verification failed: {error_code}")
        return False

    except Exception as e:
        logger.error(f"[ARVAN] Credential verification error: {e}")
        return False