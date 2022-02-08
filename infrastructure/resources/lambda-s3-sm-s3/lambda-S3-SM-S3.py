# Import packages 
import json
import boto3
import os 
import urllib
from botocore.exceptions import ClientError
from time import gmtime, strftime
import time
import re 

# Define the environment variables 
ENDPOINT = os.environ['SM_ENDPOINT']

# Define clients for services 
S = boto3.Session()
sm_runtime = S.client('runtime.sagemaker')#, region_name = AWS_REGION)
s3_client = S.client('s3')
sagemaker_client = S.client('sagemaker')


def lambda_handler(event, context):
    
    # take the result uploaded by 
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    # get the object from the summary-input bucket 
    response = s3_client.get_object(Bucket=bucket, Key=key)
    #print(f"Response parsed from {bucket}")
    
    decoded_string = response['Body'].read().decode('utf-8')
    
    decoded_dict = json.loads(decoded_string)
    
    
    item_list = decoded_dict['results']['items']
    speach_segment = decoded_dict['results']['speaker_labels']['segments'] 
    
    
    i = 0
    result = ''
    
    for segment in speach_segment: 
        #print(segment['start_time'], segment['end_time'], segment['speaker_label'])  #segment['items'])
        #print(segment['items'])
    
        speaker_laebL_List = [sub_seg_item['speaker_label'] for sub_seg_item in segment['items']]
    
        if len(set(speaker_laebL_List)) == 1: 
    
            speaker = speaker_laebL_List[0]
            label = speaker[-1]
            #print(label)
    
        else: 
    
            raise NameError('More than one speaker presented in one segment of speech')
    
        segment_start_time = segment['items'][0]['start_time']
        segment_end_time = segment['items'][-1]['end_time']
    
        result += f"speaker {label} said: "
    
        # if not reached the end of the segment, in while loop 
        end_segment_not_reached = False
        # if not reached the end of the item list, still in while loop 
    
        while not end_segment_not_reached and i < len(item_list): 
    
            if 'end_time' in item_list[i]: 
    
                if item_list[i]['end_time'] == segment_end_time: 
                
                    if i+1 < len(item_list): 
    
                        result += item_list[i]['alternatives'][0]['content']
                        
                        if item_list[i+1]['type'] == 'punctuation': 
                        
                            result += item_list[i+1]['alternatives'][0]['content'] + ' '
    
                        else: 
                            
                            result += '. '
    
                        end_segment_not_reached = True
    
                    else: 
                        
                        result += item_list[i]['alternatives'][0]['content']
                        
                        end_segment_not_reached = True
    
                else: 
    
                    result += item_list[i]['alternatives'][0]['content'] + ' '
    
            else: 
                
                result += item_list[i]['alternatives'][0]['content'] + ' '
            
            i+= 1 
    
    result = re.sub(r': .', ': ', result)
    print(len(result))
    
    segment = result#result[:round((len(result)-1)/3)]
    print(len(segment))
    
    result_dic = {"inputs" : segment}
    #print(result_dic.keys())
    
    result_dic_json = json.dumps(result_dic)
    
    sm_input_key = f'InvokeInput/processed-{key}'
    
    s3_put_response = s3_client.put_object(Body= result_dic_json.encode('utf-8'),
                         Bucket= bucket,
                         Key = sm_input_key,
                         )
    print(f"result pased and return to {bucket}")
                         
    if s3_put_response['ResponseMetadata']['HTTPStatusCode'] == 200: 
        
        s3_sm_input = f"s3://{bucket}/{sm_input_key}"
        
    else: 
        print('Processed JSON file was not put into S3 bucket successfully')
        return None 
        
    # Validate using a real-time endpoint: 
    #response = sm_runtime.invoke_endpoint(
    #                                EndpointName='huggingface-pytorch-training-2022-02-06-18-56-25-098',
    #                                Body= result_dic_json.encode('UTF-8'),
    #                                ContentType="application/json"
    #)
    
    #result_string = response['Body'].read().decode('UTF-8')
    #print(result_string)
    
    # Invoke the sagemaker Aynsc endpoint 
    response = sm_runtime.invoke_endpoint_async(
                            EndpointName=ENDPOINT,
                            InputLocation= s3_sm_input,
                            ContentType="application/json",
                                                )
    print(response)
    ouotput_s3_uri = response["OutputLocation"]
    print(f"Output from Sagemaker Async endpoint is stored in {ouotput_s3_uri}")
    
