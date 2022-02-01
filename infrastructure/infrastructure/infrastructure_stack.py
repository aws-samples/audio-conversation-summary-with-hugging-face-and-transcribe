from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as _s3,
    RemovalPolicy,
    # aws_s3_deployment as s3deploy,
    aws_dynamodb as _dynamodb,
    aws_sns as _sns,
    Environment
    
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # (VPC)

        # S3 Bucket
        bucket = _s3.Bucket(self, "text-summarization-bucket", 
                            versioned=True,
                            removal_policy=RemovalPolicy.DESTROY,
                            auto_delete_objects=True)       

        # Lambda
        my_function_handler = _lambda.Function(self,
                                               "lambda_handler",
                                               runtime=_lambda.Runtime.PYTHON_3_8,
                                               code=_lambda.Code.from_asset("resources"),
                                               handler="lambda.lambda_handler",
                                               environment={"BUCKET_NAME": bucket.bucket_name, 
                                                            # "KEY": self.node.try_get_context("s3_lexicon_key")
                                                            }
                                                            )
        bucket.grant_read_write(my_function_handler)
        
        # DynamoDB
        table = _dynamodb.Table(self, 
                                "Table", 
                                partition_key=_dynamodb.Attribute(name="id", 
                                type=_dynamodb.AttributeType.STRING)
                                )

        # SNS
        topic = _sns.Topic(self, "Topic",
                           display_name="Send Summary Topic"
                            )

        

        # SageMaker Endpoint