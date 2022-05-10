# Import packages
import json
import os
import urllib
from parser import transformer
from time import gmtime, strftime

import boto3
from botocore.exceptions import ClientError

# Define the environment variables
ENDPOINT = os.environ["SM_ENDPOINT"]

# Define clients for services
session = boto3.Session()
sm_runtime = session.client("runtime.sagemaker")  # , region_name = AWS_REGION)
s3_client = session.client("s3")
sagemaker_client = session.client("sagemaker")


def lambda_handler(event, context):

    # take the result uploaded by
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    # get the object from the summary-input bucket
    response = s3_client.get_object(Bucket=bucket, Key=key)

    decoded_string = response["Body"].read()

    decoded_dict = json.loads(decoded_string)

    language_code = "en-US"
    result = transformer(language_code, decoded_dict)
    print(len(result))

    n = 2000
    segments = [result[i: i + n] for i in range(0, len(result), n)]
    print(segments)
    print(len(segments))

    for segment in segments:

        result_dic = {"inputs": segment}

        result_dic_json = json.dumps(result_dic)

        sm_input_key = f"InvokeInput/processed-{key}"

        s3_put_response = s3_client.put_object(
            Body=result_dic_json.encode("utf-8"),
            Bucket=bucket,
            Key=sm_input_key,
        )

        if s3_put_response["ResponseMetadata"]["HTTPStatusCode"] == 200:

            s3_sm_input = f"s3://{bucket}/{sm_input_key}"

        else:
            print("Processed JSON file was not put into S3 bucket successfully")
            return None

        # Invoke the sagemaker async endpoint
        response = sm_runtime.invoke_endpoint_async(
            EndpointName=ENDPOINT,
            InputLocation=s3_sm_input,
            ContentType="application/json",
        )
        print(response)

        output_s3_uri = response["OutputLocation"]
        print(f"Output from Sagemaker Async endpoint is stored in {output_s3_uri}")
