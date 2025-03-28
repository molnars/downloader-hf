import requests
import boto3
import os
import tempfile

model_id = "nomic-ai/nomic-embed-text-v1.5" #"bert-base-uncased"  # Replace with the desired model ID
proxy_url = "http://172.24.109.67:8080"  # Replace with your proxy URL and port
bucket_name = "ods-model2"  # Replace with your S3 bucket name
s3_url="http://minio-service.nonprod-oai-app1.svc.cluster.local:9000"

def list_model_files(model_id, proxy_url):
    # Hugging Face API endpoint for model info
    url = f"https://huggingface.co/api/models/{model_id}"
    
    # Set up the proxy configuration
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        # Make a GET request to the Hugging Face API
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()  # Raise an error for bad responses
        
        # Parse the JSON response
        model_info = response.json()
        
        # Extract the list of files
        files = [file_info['rfilename'] for file_info in model_info['siblings'] if 'rfilename' in file_info]
        return files
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while retrieving model files: {e}")
        return []

def download_file(file_url, proxy_url):
    try:
        # Set up the proxy configuration
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Make a GET request to download the file
        response = requests.get(file_url, proxies=proxies)
        response.raise_for_status()  # Raise an error for bad responses
        
        return response.content
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading file {file_url}: {e}")
        return None

def upload_to_s3(file_content, file_name, bucket_name, s3_client):
    try:
        # Upload the file content to the S3 bucket
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
        print(f"Successfully uploaded {file_name} to {bucket_name}")
    
    except Exception as e:
        print(f"An error occurred while uploading {file_name} to {bucket_name}: {e}")

if __name__ == "__main__":

    access_key = "<<REPLACEME>>"
    secret_key = "<<REPLACEME>>"
    s3_client = boto3.client('s3', endpoint_url=s3_url, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    
    # List model files
    files = list_model_files(model_id, proxy_url)
	
    if not files:
        print("No files to download.")
        exit(1)
    print(f"{model_id} has {len(files)} number of items")
    
    # Temporary directory to store downloaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        for file_name in files:
            # Construct the file URL
            file_url = f"https://huggingface.co/{model_id}/resolve/main/{file_name}"
            
            # Download the file
            file_content = download_file(file_url, proxy_url)
            
            if file_content is not None:
                # Upload the file to S3
                upload_to_s3(file_content, f"models/{model_id}/{file_name}", bucket_name, s3_client)
    print(f"upload done")
