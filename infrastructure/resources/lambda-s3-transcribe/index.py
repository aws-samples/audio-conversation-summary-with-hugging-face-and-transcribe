import json
import boto3 
import os 
import urllib
import gzip
from botocore.exceptions import ClientError
from datetime import datetime
import time
#from time import gmtime, strftime
#import time


# Define the environment variables 
#ENDPOINT = os.environ['Sagemaker_Endpoint']
#AWS_REGION =  os.environ['AWS_Region']

# Define clients for services 
S = boto3.Session()
#sm_runtime = S.client('runtime.sagemaker')#, region_name = AWS_REGION)
s3_client = S.client('s3')
ts_client = S.client('transcribe')


def lambda_handler_s3_transcribe(event, context):
    
    
    # take the result from the export from the DynamoDB 
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    #print(key)

    input_s3_uri = f"s3://{bucket}/{key}"
    
    now = datetime.now()
    current_time = now.strftime("%H-%M-%S")
    #print(current_time)
    job_name = f"job{current_time}"
    
    ts_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': input_s3_uri},
        MediaFormat='mp4',
        LanguageCode='en-US', 
        Settings = {
              'ChannelIdentification': False,
              'ShowSpeakerLabels': True,
              'MaxSpeakerLabels': 10,
              },
              
        OutputBucketName='summary-transcript',
        OutputKey='TranscribeOutput/',
        )
    
    
# print the result in the terminal, make sure you get the S3 URL to download the transcript JSON file
 