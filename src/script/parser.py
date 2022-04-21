def diarizer(language_code, data): 

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
    counter = 0 
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
                            #if the sentencte ends with a ouncuation 
                        
                            result += item_list[i+1]['alternatives'][0]['content'] + ' '

                        else: 
                            #if the sentence does not end with a punctuation
                            
                            result += ' '
                            #result += space + item_list[i+1]['alternatives'][0]['content'] + '.'

                    else: 
                        
                        result += space +  item_list[i]['alternatives'][0]['content'] + '.'
                        
                    #i += 1
                    end_segment_not_reached = True

                else: 

                    if item_list[i]['type'] == 'punctuation':

                        result +=  item_list[i]['alternatives'][0]['content'] 

                    else: 
                        
                        result +=  space + item_list[i]['alternatives'][0]['content'] 


            else: 
                
                result += item_list[i]['alternatives'][0]['content'] 
            
            i+= 1 

    #result = re.sub(r': .', ': ', result)
    return result


