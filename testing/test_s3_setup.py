#!/usr/bin/env python3
"""
Simple test script to verify S3 bucket connection
Run this after setting up your .env file
"""

import boto3
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_s3_connection():
    """Test S3 bucket connection and permissions"""
    
    # Get configuration from environment
    bucket_name = os.getenv('S3_CONVERSATION_BUCKET', 'cliox-chatbot-conversations')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    
    print(f"🧪 Testing S3 connection to bucket: {bucket_name}")
    print(f"📍 Region: {region}")
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )
        
        # Test 1: List bucket (check access)
        print("\n✅ Test 1: Checking bucket access...")
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print("✅ Bucket access successful!")
        
        # Test 2: Write test file
        print("\n✅ Test 2: Testing write permissions...")
        test_data = {
            "test": "S3 connection working",
            "timestamp": datetime.now().isoformat(),
            "bucket": bucket_name
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key="test/connection_test.json",
            Body=json.dumps(test_data, indent=2),
            ContentType="application/json",
            ServerSideEncryption="AES256"  # Explicitly use SSE-S3 encryption
        )
        print("✅ Write test successful!")
        
        # Test 3: Read test file
        print("\n✅ Test 3: Testing read permissions...")
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key="test/connection_test.json"
        )
        
        content = json.loads(response['Body'].read())
        print(f"✅ Read test successful! Content: {content['test']}")
        
        # Test 4: Delete test file
        print("\n✅ Test 4: Testing delete permissions...")
        s3_client.delete_object(
            Bucket=bucket_name,
            Key="test/connection_test.json"
        )
        print("✅ Delete test successful!")
        
        print("\n🎉 All S3 tests passed! Your bucket is ready for conversation storage.")
        
    except Exception as e:
        print(f"\n❌ S3 test failed: {e}")
        print("\n🔧 Check:")
        print("  1. AWS credentials in .env file")
        print("  2. Bucket name is correct") 
        print("  3. IAM user has proper permissions")
        print("  4. Bucket exists and is in the correct region")
        return False
    
    return True

if __name__ == "__main__":
    success = test_s3_connection()
    exit(0 if success else 1)
