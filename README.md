# Text Summarization


<center>
    <img src="AD.png" width=1000/>
</center>

---

## What is the Problem being addressed in this Project ?

The vast amount of virtual meetings an AWS employee has to attend on a daily basis can be overwhelming and makes it difficult to remember all of the important aspects that have been discussed. One option to handle this issue is to manually take notes during the meeting which nonetheless greatly reduces the capacity to pay attention and hence renders it suboptimal. Instead it would be more effective if the meeting would be automatically summarized leveraging technologies such as Machine Learning and Natural Language Processing. That way every attendee can pay attention to the conversation in the meeting while still being able to check on certain discussed topics on a summarized transcript at a later point in time. 

This project aims at providing a possible solution for the aforementioned problem using Standard AWS Services as exhibited below in the Architecture Diagram.

## What is the proposed Solution?

In this project an application has been developed that is able to summarize a discussion from a virtual meeting (eg. through Amazon Chime) with several participants. The only prerequisite is a transcript of the recorded meeting which can easily be created using Amazon Transcribe, a fully managed service that allows to convert speech into text with a single API call. Once the transcript has been created it can be stored in DynamoDB. From there it can be exported to S3, which will then trigger a Lambda function that will fetch the recording and transform it into JSON format. Subsequently the Lambda function invokes a SageMaker Endpoint that will use the JSON file as an input and generate a prediction and store it in an S3 bucket. In a last step the predicted summary is sent to the meeting attendees through SNS.

## How can this Project be used?

<!-- For this application, all services have been provisioned on the AWS Console and hence no IaC script is currently available. Nonetheless we provide all the details needed to recreate the application quickly in a new account. This includes an Architecture Diagram and multiple code scripts used for the Lambda function as well as data preprocessing and training scripts. Finally we also provide the input data to train, validate and test the model. -->
This project provides Infrastructure-as-Code (IaC) scripts based on AWS CDK written in Python language. This can be used to deploy all resources to a specified account and region and allows to test the application only within a few minutes. If you haven't used CDK before checkout the AWS developer guide https://docs.aws.amazon.com/cdk/v2/guide/home.html and make sure to install the cdk library and toolkitA clear set of guidelines for deployment are provided below under **How to deploy the CDK Stack (Mac OS) ?**

### How to setup your coding Environment?

1. Download latest version of Python 3: https://www.python.org/downloads/
2. Download Visual Studio Code: https://code.visualstudio.com
3. Clone the git repository: https://gitlab.aws.dev/sentichime/text-summarization.git

### How to deploy the CDK Stack (Mac OS)?

First "cd" into the infrastructure directory and setup your virtual environment using python
```
python3 -m venv .venv
```

Activate the virtual environment: 
```
source .venv/bin/activate
```
Install the required packages:

```
pip install -r requirements.txt
```

Assume your isengard account
```
isengardcli assume
```

If you run cdk for the first time in your account and region you specified, you need to bootstrap cdk first:
```
cdk bootstrap
```

At this point you can now synthesize the CloudFormation template for this code:
```
cdk synth
```

When making infrastructure adjustment you can check the differences before deploying by running the cdk diff command:
```
cdk diff
```
To deploy the content you can run the cdk deploy command:
```
cdk deploy
```

In order to destroy the stack, you can call the cdk destroy command:
```
cdk destroy
```

### Testing
In order to allow for rapid testing of the application a simple .mp4 file has been provided which captures a conversation between 2 people recorded on Amazon Chime. The data is stored under the data/ directory. Before running the application it is necessary to first specify the email address which will subscribe to the SNS topic and hence receive the meeting summary. This can be done by updating the entry in **email_addresses.json** file. Once that has been done the mp4 file must be uploaded to the S3 BucketRecordings bucket, which will trigger the application.
