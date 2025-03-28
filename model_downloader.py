import requests
import boto3
import os
import tempfile

model_id = os.getenv("MODEL_ID","nomic-ai/nomic-embed-text-v1.5") #"bert-base-uncased"  # Replace with the desired model ID
proxy_url = os.getenv("HTTPS_PROXY","http://172.24.109.67:8080")  # Replace with your proxy URL and port
bucket_name = os.getenv("MODEL_BUCKET","ods-model2")  # Replace with your S3 bucket name
s3_url=os.getenv("S3_ENDPOINT_URL","http://minio-service.nonprod-oai-app1.svc.cluster.local:9000")
proxies = None
models_dir = os.getenv("MODEL_DIR","models")
hf_token = os.getenv("HF_TOKEN","")
headers = {}
count =0

def list_model_files(model_id, proxy_url):
    # Hugging Face API endpoint for model info
    url = f"https://huggingface.co/api/models/{model_id}"
    
    # Set up the proxy configuration
    #proxies = {'http': proxy_url,'https': proxy_url} if proxy_url else None
    
    try:
        # Make a GET request to the Hugging Face API
        response = requests.get(url, headers=headers, proxies=proxies)
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
        #proxies = {'http': proxy_url,'https': proxy_url} if proxy_url else None
        #proxies = {
        #    'http': proxy_url,
        #    'https': proxy_url
        #}
        
        # Make a GET request to download the file
        response = requests.get(file_url, headers=headers, proxies=proxies)
        response.raise_for_status()  # Raise an error for bad responses
        
        return response.content
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading file {file_url}: {e}")
        return None

def upload_to_s3(file_content, file_name, bucket_name, s3_client):
    try:
        # Upload the file content to the S3 bucket
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
        print(f"Successfully uploaded {count} - {file_name} to {bucket_name}")
    
    except Exception as e:
        print(f"An error occurred while uploading {count} - {file_name} to {bucket_name}: {e}")

if __name__ == "__main__":

    access_key = os.getenv("AWS_ACCESS_KEY","<<REPLACEME>>")
    secret_key = os.getenv("AWS_SECRET_KEY","<<REPLACEME>>")
    s3_client = boto3.client('s3', endpoint_url=s3_url, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    proxies = {'http': proxy_url,'https': proxy_url} if proxy_url else None
    if hf_token:
         headers['Authorization'] = f'Bearer: {hf_token}'
	
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
            count = count +1
            # Download the file
            file_content = download_file(file_url, proxy_url)
            
            if file_content is not None:
                # Upload the file to S3
                upload_to_s3(file_content, f"{models_dir}/{model_id}/{file_name}", bucket_name, s3_client)
    print(f"upload done")
