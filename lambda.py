# Import packages 
import json
import boto3
import os 
import json
import urllib
import gzip
from botocore.exceptions import ClientError
from time import gmtime, strftime
import time

# Define the environment variables 
ENDPOINT = os.environ['Sagemaker_Endpoint']
AWS_REGION =  os.environ['AWS_Region']

# Define clients for services 
S = boto3.Session()
sm_runtime = S.client('runtime.sagemaker', region_name = AWS_REGION)
s3_client = S.client('s3')
sagemaker = S.client('sagemaker')

def lambda_handler(event, context):
    
    # take the result from the export from the DynamoDB 
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    # get the object from the summary-input bucket 
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Decode the byte (from response) into a string containing all the meeting summary 
    with gzip.GzipFile(fileobj=response["Body"]) as gzipfile:
        content = gzipfile.read().decode('UTF-8')
    
    # Seperate the string into multipl lines
    content_list = content.splitlines()
    
    # Build a result dictonary exactly the same format as the train/test data-set of the model 
    result = {'text':''}
    for i in range(len(content_list)): 
    
        string = """
        """
        string += content_list[i]
    
        dic = json.loads(string)
    
        item = dic['Item']
    
        sentence = 'speaker' + ' ' + item['speaker_label']['S'] + ':' + item['content']['S'] + ' '
    
        result['text'] += sentence
        
    length = len(result['text'])
    text = result['text']
            
    dic = {"inputs" : text}
    dic_json = json.dumps(dic)
    
    body = dic_json.encode('UTF-8') 
    
    current_timestamp = strftime("%m-%d-%H-%M", gmtime())
    key = f"ProcessedOuput/processed-ouput-{current_timestamp}.json"
    
    # Download it into the another prefix in the same S3 bucket 
    # put the object into the input summary bucket 
    s3_put_response = s3_client.put_object(Body= body,
                         Bucket= bucket,
                         Key = key,
    )
                         
    if s3_put_response['ResponseMetadata']['HTTPStatusCode'] == 200: 
        
        s3_sm_input = f"s3://{bucket}/{key}"
        
    else: 
        print('Processed JSON file was not put into S3 bucket successfully')
        return None 
    
    # Invoke the sagemaker Aynsc endpoint 
    response = sm_runtime.invoke_endpoint_async(
                            EndpointName=ENDPOINT,
                            InputLocation= s3_sm_input,
                            ContentType="application/json",
    )
    
    ouotput_s3_uri = response["OutputLocation"]
    print(ouotput_s3_uri)

    # As the invokation might take some time, we need to query the status of the S3 bucket
    def get_output(ouotput_s3_uri):
        
        bucket_prefix = ouotput_s3_uri.split('//')[1]
        
        bucket = bucket_prefix.split('/')[0]
        print(bucket)
        key = '/'.join(bucket_prefix.split('/')[1:])
        print(key)
        
        while True:
            try:
                # Only need get_object from the ouput bucket 
                response = s3_client.get_object(Bucket = bucket, Key = key)
                # Decode the byte (from response) into a string containing all the meeting summary 
                content = json.loads(response['Body'].read())
                
                return content 
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    print("waiting for output...")
                    time.sleep(2)
                    continue
                raise
            
    content = get_output(ouotput_s3_uri) 
    print(content)
    
    return send_request(content[0]['summary_text'])
    
def send_request(body):
    
    # Create an SNS client
    sns = boto3.client('sns')
 
    # Publish a simple message to the specified SNS topic
    response = sns.publish(
        TopicArn=os.environ['EMAIL_TOPIC_ARN'],    
        Message=body,    
    )
 
    # Print out the response
    print(response)
              