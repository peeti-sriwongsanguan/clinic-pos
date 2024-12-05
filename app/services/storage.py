import boto3
from config import Config


class StorageService:
    def __init__(self):
        self.s3 = boto3.client('s3',
                               region_name=Config.AWS_REGION)
        self.bucket = Config.S3_BUCKET

    def upload_file(self, file_path, object_name):
        try:
            self.s3.upload_file(file_path, self.bucket, object_name)
            return f"https://{self.bucket}.s3.amazonaws.com/{object_name}"
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            raise