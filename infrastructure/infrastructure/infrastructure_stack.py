from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as _s3,
    RemovalPolicy,
    # aws_s3_deployment as s3deploy,
    aws_dynamodb as _dynamodb,
    aws_sns as _sns,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    Environment,
)
from constructs import Construct

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

iam_sagemaker_actions = [
    "sagemaker:*",
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

        # (VPC)

        # S3 Bucket
        bucket = _s3.Bucket(
            self,
            "text-summarization-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Lambda
        my_function_handler = _lambda.Function(
            self,
            "lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("resources"),
            handler="lambda.lambda_handler",
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                # "KEY": self.node.try_get_context("s3_lexicon_key")
            },
        )
        bucket.grant_read_write(my_function_handler)

        # DynamoDB
        table = _dynamodb.Table(
            self,
            "Table",
            partition_key=_dynamodb.Attribute(
                name="id", type=_dynamodb.AttributeType.STRING
            ),
        )

        # SNS
        topic = _sns.Topic(self, "Topic", display_name="Send Summary Topic")

       # SageMaker Endpoint 
        summary_bucket = _s3.Bucket(self, "summary-bucket")
        huggingface_model = "google/pegasus-large"
        huggingface_task = "summarization"
        instance_type = "ml.m5.xlarge"
        model_name = "senti-chime-model"
        endpoint_config_name = "senti-chime-endpoint-config"
        endpoint_name = "senti-chime-endpoint"

        role = iam.Role(
            self,
            "hf_sagemaker_execution_role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )
        role.add_to_policy(
            iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions)
        )

        image_uri = get_image_uri(region=kwargs["env"].region)
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
                    s3_output_path=summary_bucket.url_for_object()
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
