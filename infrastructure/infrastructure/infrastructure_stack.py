# This is the infra stack for Meeting Summary
import json
import boto3
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as _s3
from aws_cdk import aws_s3_notifications as s3_notify
from aws_cdk import aws_sagemaker as sagemaker
from aws_cdk import aws_sns as _sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import CfnParameter 
from aws_cdk import Fn
from constructs import Construct

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]

LATEST_PYTORCH_VERSION = "1.8.1"
LATEST_TRANSFORMERS_VERSION = "4.10.2"

region_dict = {
    "af-south-1": "626614931356",
    "ap-east-1": "871362719292",
    "ap-northeast-1": "763104351884",
    "ap-northeast-2": "763104351884",
    "ap-northeast-3": "364406365360",
    "ap-south-1": "763104351884",
    "ap-southeast-1": "763104351884",
    "ap-southeast-2": "763104351884",
    "ca-central-1": "763104351884",
    "cn-north-1": "727897471807",
    "cn-northwest-1": "727897471807",
    "eu-central-1": "763104351884",
    "eu-north-1": "763104351884",
    "eu-south-1": "692866216735",
    "eu-west-1": "763104351884",
    "eu-west-2": "763104351884",
    "eu-west-3": "763104351884",
    "me-south-1": "217643126080",
    "sa-east-1": "763104351884",
    "us-east-1": "763104351884",
    "us-east-2": "763104351884",
    "us-gov-west-1": "442386744353",
    "us-iso-east-1": "886529160074",
    "us-west-1": "763104351884",
    "us-west-2": "763104351884",
}


def get_image_uri(
    region=None,
    transformmers_version=LATEST_TRANSFORMERS_VERSION,
    pytorch_version=LATEST_PYTORCH_VERSION,
):
    repository = f"{region_dict[region]}.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-inference"
    tag = f"{pytorch_version}-transformers{transformmers_version}-{'cpu-py36'}-ubuntu18.04"
    return f"{repository}:{tag}"


class InfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        account_region = kwargs["env"].region

        # S3 Buckets
        bucket_recordings = _s3.Bucket(
            self,
            "BucketRecordings",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            encryption=_s3.BucketEncryption.S3_MANAGED,
            server_access_logs_prefix="Server-Access-Logs",
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
        )

        bucket_transcriptions = _s3.Bucket(
            self,
            "BucketTranscriptions",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            encryption=_s3.BucketEncryption.S3_MANAGED,
            server_access_logs_prefix="Server-Access-Logs",
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
        )

        bucket_predictions = _s3.Bucket(
            self,
            "BucketPredictions",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            encryption=_s3.BucketEncryption.S3_MANAGED,
            server_access_logs_prefix="Server-Access-Logs",
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
        )

        # Add the Encyption Key for SNS Server Side Encryption
        SNS_encryption_key = kms.Key(self, "Key", enable_key_rotation=True)

        # SNS
        topic = _sns.Topic(
            self,
            "MeetingSummary",
            display_name="MeetingSummary",
            master_key=SNS_encryption_key,
        )


        emails = CfnParameter(
            self, 
            "ParticipatorEmailAddress", 
            type="CommaDelimitedList",
            description="The e-mail addresses of those who attended the meeting (list seperated with comma)"
        )

        email_list = emails.value_as_list

        for i in range(len(email_list)):
            topic.add_subscription(
                sns_subscriptions.EmailSubscription(Fn.select(i, email_list))
             )

        # SageMaker Endpoint
        huggingface_model = "linydub/bart-large-samsum"
        huggingface_task = "summarization"
        instance_type = "ml.m5.large"  # "ml.m5.xlarge"
        model_name = "bart-large-summarization-model"
        endpoint_config_name = "bart-large-summarization-endpoint-config"
        endpoint_name = "bart-large-summarization-endpoint"

        role = iam.Role(
            self,
            "hf_sagemaker_execution_role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

        iam_sagemaker_actions = [
            "sagemaker:CreateEndpoint",
            "sagemaker:CreateEndpointConfig",
            "sagemaker:InvokeEndpoint",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetAuthorizationToken",
            "cloudwatch:PutMetricData",
            "cloudwatch:GetMetricData",
            "cloudwatch:GetMetricStatistics",
            "cloudwatch:ListMetrics",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:DescribeLogStreams",
            "logs:PutLogEvents",
            "logs:GetLogEvents",
            "s3:CreateBucket",
            "s3:ListBucket",
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:PutObject",
        ]

        role.add_to_policy(
            iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions)
        )

        image_uri = get_image_uri(account_region)

        container_environment = {
            "HF_MODEL_ID": huggingface_model,
            "HF_TASK": huggingface_task,
        }

        container = sagemaker.CfnModel.ContainerDefinitionProperty(
            environment=container_environment, image=image_uri
        )

        model = sagemaker.CfnModel(
            self,
            "hf_model",
            execution_role_arn=role.role_arn,
            primary_container=container,
            model_name=model_name,
        )

        endpoint_configuration = sagemaker.CfnEndpointConfig(
            self,
            "hf_endpoint_config",
            endpoint_config_name=endpoint_config_name,
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    initial_instance_count=1,
                    instance_type=instance_type,
                    model_name=model.model_name,
                    initial_variant_weight=1.0,
                    variant_name=model.model_name,
                )
            ],
            async_inference_config=sagemaker.CfnEndpointConfig.AsyncInferenceConfigProperty(
                output_config=sagemaker.CfnEndpointConfig.AsyncInferenceOutputConfigProperty(
                    s3_output_path=bucket_predictions.url_for_object()
                ),
            ),
        )

        endpoint = sagemaker.CfnEndpoint(
            self,
            "summarization_endpoint",
            endpoint_name=endpoint_name,
            endpoint_config_name=endpoint_configuration.endpoint_config_name,
        )

        endpoint_configuration.add_depends_on(model)
        endpoint.add_depends_on(endpoint_configuration)

        # Lambda: s3_transcribe
        transcribe_lambda = _lambda.Function(
            self,
            "LambdaS3Transcribe",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("resources/lambda-s3-transcribe"),
            handler="index.lambda_handler",
            environment={
                "BUCKET_NAME": bucket_transcriptions.bucket_name,
            },
        )

        # Permissions
        bucket_recordings.grant_read_write(transcribe_lambda)
        transcribe_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogGroup"],
                resources=[f"arn:aws:logs:{account_region}:{account_id}:*"],
            )
        )

        transcribe_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{account_region}:{account_id}:log-group:/aws/lambda/LambdaS3Transcribe:*"
                ],
            )
        )

        transcribe_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "transcribe:GetTranscriptionJob",
                    "transcribe:StartTranscriptionJob",
                ],
                resources=["*"],
            )
        )

        # Trigger
        notification_recordings = s3_notify.LambdaDestination(
            transcribe_lambda
        )
        notification_recordings.bind(self, bucket_recordings)

        for suffix in [".mp4", ".mp3", ".wav", ".m4a"]:
            bucket_recordings.add_object_created_notification(
                notification_recordings, _s3.NotificationKeyFilter(suffix=suffix)
            )

        # Lambda: s3-sm-s3
        inference_lambda = _lambda.Function(
            self,
            "LambdaS3SageMakerS3",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("resources/lambda-s3-sm-s3"),
            handler="index.lambda_handler",
            environment={
                "BUCKET_NAME": bucket_transcriptions.bucket_name,
                "SM_ENDPOINT": endpoint.endpoint_name
            },
        )

        # Permissions
        bucket_transcriptions.grant_read_write(inference_lambda)
        bucket_transcriptions.grant_read_write(transcribe_lambda)

        inference_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogGroup"],
                resources=[f"arn:aws:logs:{account_region}:{account_id}:*"],
            )
        )

        inference_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{account_region}:{account_id}:log-group:/aws/lambda/LambdaS3SageMakerS3:*"
                ],
            )
        )

        inference_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:InvokeEndpointAsync"],
                resources=[
                    f"arn:aws:sagemaker:{account_region}:{account_id}:endpoint/{endpoint.endpoint_name}"
                ],
            )
        )

        # Trigger
        notification_transcriptions = s3_notify.LambdaDestination(
            inference_lambda
        )
        notification_transcriptions.bind(self, bucket_transcriptions)
        bucket_transcriptions.add_object_created_notification(
            notification_transcriptions,
            _s3.NotificationKeyFilter(suffix=".json", prefix="TranscribeOutput/"),
        )

        # Lambda: s3-sns
        my_function_handler_s3_sns = _lambda.Function(
            self,
            "LambdaS3SNS",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("resources/lambda-s3-sns"),
            handler="index.lambda_handler",
            environment={
                "BUCKET_NAME": bucket_predictions.bucket_name,
                "EMAIL_TOPIC_ARN": topic.topic_arn
                # "KEY": self.node.try_get_context("s3_lexicon_key")
            },
        )

        # Permissions
        bucket_predictions.grant_read_write(my_function_handler_s3_sns)

        my_function_handler_s3_sns.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogGroup"],
                resources=[f"arn:aws:logs:{account_region}:{account_id}:*"],
            )
        )

        my_function_handler_s3_sns.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{account_region}:{account_id}:log-group:/aws/lambda/LambdaS3SNS:*"
                ],
            )
        )

        my_function_handler_s3_sns.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sns:Publish"],
                resources=[topic.topic_arn],
            )
        )

        my_function_handler_s3_sns.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["kms:GenerateDataKey", "kms:Decrypt"],
                resources=[SNS_encryption_key.key_arn],
            )
        )

        # Trigger
        notification_predictions = s3_notify.LambdaDestination(
            my_function_handler_s3_sns
        )
        notification_predictions.bind(self, bucket_predictions)
        bucket_predictions.add_object_created_notification(
            notification_predictions, _s3.NotificationKeyFilter(suffix=".out")
        )
