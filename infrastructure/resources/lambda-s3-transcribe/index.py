import gzip
import json
import os
import time
import urllib
from datetime import datetime

import boto3

# Define clients for services
session = boto3.Session()
s3_client = session.client("s3")
ts_client = session.client("transcribe")

BUCKET_NAME = os.environ.get("BUCKET_NAME")


def lambda_handler(event, context):

    # take the result from the export from the DynamoDB
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    # print(key)

    format = key.split(".")[-1]
    if format in ["m4a", "mp4"]:
        mediaformat = "mp4"

    if format in ["wav"]:
        mediaformat = "wav"

    if format in ["mp3"]:
        mediaformat = "mp3"

    input_s3_uri = f"s3://{bucket}/{key}"

    now = datetime.now()
    current_time = now.strftime("%H-%M-%S")
    # print(current_time)
    job_name = f"job{current_time}"

    ts_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": input_s3_uri},
        MediaFormat=mediaformat,
        LanguageCode="en-US",
        Settings={
            "ChannelIdentification": False,
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": 2,
        },
        OutputBucketName=BUCKET_NAME,
        OutputKey="TranscribeOutput/",
    )
