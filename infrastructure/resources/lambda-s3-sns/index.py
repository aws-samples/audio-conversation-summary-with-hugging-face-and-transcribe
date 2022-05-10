import json
import os
import urllib

import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    # get the object from the summary-input bucket
    response = s3.get_object(Bucket=bucket, Key=key)

    content = json.loads(response["Body"].read())
    content_dic = content[0]

    print(content_dic)

    if "summary_text" in content_dic:
        response = send_request(content[0]["summary_text"])
    elif "generated_text" in content_dic:
        response = send_request(content[0]["generated_text"])
    else:
        response = send_request(content[0])


def send_request(body):

    # Create an SNS client
    sns = boto3.client("sns")

    # Publish a simple message to the specified SNS topic
    response = sns.publish(
        TopicArn=os.environ["EMAIL_TOPIC_ARN"],
        Message=body,
    )

    # Print out the response
    print(response)
