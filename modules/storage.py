import boto3
import json
import os
from botocore.exceptions import ClientError
# Add config import if needed for any default values
from .config import get_config

class S3Helper:
    def __init__(self, bucket, prefix_root):
        self.bucket = bucket
        self.prefix_root = prefix_root
        self.s3 = boto3.client('s3')
    
    def _get_script_key(self, request_id, script_type, status_folder):
        """Generate S3 key for a script"""
        return f"{self.prefix_root}/{status_folder}/{request_id}/{script_type}.sql"
    
    def put_script(self, request_id, dataset, script_type, content):
        """Upload a script to S3 under the pending folder"""
        key = self._get_script_key(request_id, script_type, "pending")
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                Metadata={
                    'dataset': dataset,
                    'type': script_type
                }
            )
            return True, key
        except ClientError as e:
            return False, str(e)
    
    def list_scripts(self, request_id, status_folder):
        """List all scripts for a request"""
        prefix = f"{self.prefix_root}/{status_folder}/{request_id}/"
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            return []
    
    def get_script(self, request_id, script_type, status_folder):
        """Get the content of a script"""
        key = self._get_script_key(request_id, script_type, status_folder)
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=key
            )
            return True, response['Body'].read().decode('utf-8')
        except ClientError as e:
            return False, str(e)
    
    def move_scripts(self, request_id, status_from, status_to):
        """Move scripts from one status folder to another"""
        script_keys = self.list_scripts(request_id, status_from)
        
        if not script_keys:
            return False, "No scripts found"
        
        success = True
        errors = []
        
        for source_key in script_keys:
            # Get the script name from the source key
            script_name = os.path.basename(source_key)
            dest_key = f"{self.prefix_root}/{status_to}/{request_id}/{script_name}"
            
            try:
                # Copy the object to the new location
                self.s3.copy_object(
                    Bucket=self.bucket,
                    CopySource={'Bucket': self.bucket, 'Key': source_key},
                    Key=dest_key
                )
                
                # Delete the original object
                self.s3.delete_object(
                    Bucket=self.bucket,
                    Key=source_key
                )
            except ClientError as e:
                success = False
                errors.append(str(e))
        
        if success:
            return True, "All scripts moved successfully"
        else:
            return False, "; ".join(errors)
