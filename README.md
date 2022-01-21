# Text Summarization

## Background 

### What is the Problem being addressed in this Project ?

The vast amount of virtual meetings an AWS employee has to attend on a daily basis can be overwhelming and makes it difficult to remember all of the important aspects that have been discussed. One option to handle this issue is to manually take notes during the meeting which nonetheless greatly reduces the capacity to pay attention and hence renders it suboptimal. Instead it would be more effective if the meeting would be automatically summarized leveraging technologies such as Machine Learning and Natural Language Processing. That way every attendee can pay attention to the conversation in the meeting while still being able to check on certain discussed topics on a summarized transcript at a later point in time. 

This project aims at providing a possible solution for the aforementioned problem using Standard AWS Services as exhibited below in the Architecture Diagram.

## Project Information

### What is the proposed Solution?

In this project an application has been developed that is able to summarize a discussion from a virtual meeting (eg. through Amazon Chime) with several participants. The only prerequisite is a transcript of the recorded meeting which can easily be created using Amazon Transcribe, a fully managed service that allows to convert speech into text with a single API call. Once the transcript has been created it can be stored in DynamoDB. From there it can be exported to S3, which will then trigger a Lambda function that will fetch the recording and transform it into JSON format. Subsequently the Lambda function invokes a SageMaker Endpoint that will use the JSON file as an input and generate a prediction and store it in an S3 bucket. In a last step the predicted summary is sent to the meeting attendees through SNS.

### How can this Project be used?

For this application, all services have been provisioned on the AWS Console and hence no IaC script is currently available. Nonetheless we provide all the details needed to recreate the application quickly in a new account. This includes an Architecture Diagram and multiple code scripts used for the Lambda function as well as data preprocessing and training scripts. Finally we also provide the input data to train, validate and test the model.

### Architecture Diagram

<!-- <center> -->
<img src="Architecture Diagram.png" width=600/>
<!-- </center> -->

## Repository

### How to setup your coding Environment (assuming you use a MAC OS) ?

Run the following commands in your terminal after having cloned the repository.

1. Download latest version of Python: https://www.python.org/downloads/ (This project was set up with python version 3.9.7)
2. Download Visual Studio Code: https://code.visualstudio.com
3. Clone the git repository: https://gitlab.aws.dev/garoga/time-series-encodings
3. Create a virtual environment locally:
```
python3 -m venv .venv
```
4. Activate the virtual environment: 
```
source .venv/bin/activate
```
5. Install the required packages:

```
pip install -r requirements.txt
```

### Data
 Few words about the data used ...