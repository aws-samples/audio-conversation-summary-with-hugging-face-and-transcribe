import boto3 
import os
import json

def transformer(language_code, data): 

    item_list = data['results']['items']
    speach_segment = data['results']['speaker_labels']['segments'] 

    if language_code == 'zh-CN': 
        space = ''
    else: 
        space = ' '

    item_list = data['results']['items']
    speach_segment = data['results']['speaker_labels']['segments'] 

    i = 0
    # All the speaker label in the same segment is produced by the same speaker 
    result = ''

    for segment in speach_segment: 

        speaker_laebL_List = [sub_seg_item['speaker_label'] for sub_seg_item in segment['items']]

        if len(set(speaker_laebL_List)) == 1: 

            speaker = speaker_laebL_List[0]
            label = speaker[-1]

        else: 

            raise NameError('Error: More than one speaker presented in one segment of speech, response from Transcribe contians error')

        #segment_start_time = segment['items'][0]['start_time']
        segment_end_time = segment['items'][-1]['end_time']

        result += f"Speaker_{label}:"

        # if not reached the end of the segment, in while loop 
        end_segment_not_reached = False
        # if not reached the end of the item list, still in while loop 

        while not end_segment_not_reached and i < len(item_list): 

            if 'end_time' in item_list[i]: 

                if item_list[i]['end_time'] == segment_end_time: 
                
                    if i+1 < len(item_list)-1: 

                        result += space + item_list[i]['alternatives'][0]['content']
                        
                        if item_list[i+1]['type'] == 'punctuation': 
                            #if the sentencte ends with a puncuation 
                        
                            result += item_list[i+1]['alternatives'][0]['content'] + ' '
                            i += 1 

                        else: 
                            #if the sentence doesn't end with a punctuation
                            
                            result += ' '
                            #result += space + item_list[i+1]['alternatives'][0]['content'] + '.'

                    else: 
                        
                        result += space +  item_list[i]['alternatives'][0]['content'] + '.'
                        
                    end_segment_not_reached = True

                else: 

                    if item_list[i]['type'] == 'punctuation':

                        result +=  item_list[i]['alternatives'][0]['content'] 

                    else: 
                        
                        result +=  space + item_list[i]['alternatives'][0]['content'] 
            else: 
                result += item_list[i]['alternatives'][0]['content'] 
            
            i+= 1 
            
    return result

if __name__ == "__main__": 

    S = boto3.Session(
        
        #aws_access_key_id = os.environ('')
    )

    s3_client = S.client("s3")

    bucket = 'text-summarization-infra-buckettranscriptions97f4-1de5eyqdi9h16'
    key = 'TranscribeOutput/job13-30-56.json'

    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    decoded_string = response['Body'].read()
    
    decoded_dict = json.loads(decoded_string)
    
    language_code = 'en-US'
    result = transformer(language_code, decoded_dict)
    print(result)
    

