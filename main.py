#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_object import S3Object
from cdktf_cdktf_provider_aws.s3_bucket_public_access_block import S3BucketPublicAccessBlock
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.s3_bucket_versioning import S3BucketVersioningA, S3BucketVersioningVersioningConfiguration
import time

AWS_REGION="eu-central-1"
S3_BUCKET_NAME="cdk-python-static-website-demo"
S3_INDEX_FILE_NAME="index.html"

class StaticWebsite(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "AWS", region=AWS_REGION)

        # Create S3 bucket
        website_bucket = S3Bucket(self, "static_website",
            bucket=S3_BUCKET_NAME
        )

        # Enable versioning of S3 bucket
        S3BucketVersioningA(self, "enable_versioning",
            bucket=website_bucket.id,
            versioning_configuration=S3BucketVersioningVersioningConfiguration(
                status="Enabled"
            )
        )

        # Allow public access to S3 bucket
        S3BucketPublicAccessBlock(self, "allow",
            bucket=website_bucket.id,
            block_public_acls=False,
            block_public_policy=False,
        )

        # Configure bucket policy for public access
        S3BucketPolicy(self, "allow_public_access",
            bucket=website_bucket.id,
            policy=f'''
            {{
                "Version": "2012-10-17",
                "Statement": [
                    {{
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::{website_bucket.id}/*"
                    }},
                    {{
                        "Sid": "BlockNonHttps",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::{website_bucket.id}/*",
                        "Condition": {{
                            "Bool": {{
                                "aws:SecureTransport": "false"
                            }}
                        }}
                    }}
                ]
            }}
            '''
        )

        # Build website's HTML contents
        html_content = """
        <html>
        <head>
        </head>
        <body>
        <h1>Hello DevOps {{ timestamp }}</h1>
        </body>
        </html>
        """

        current_timestamp = str(int(time.time()))
        html_content = html_content.replace("{{ timestamp }}", current_timestamp)

        # Create index page object in S3 bucket
        S3Object(self, "static_website_index",
            bucket=website_bucket.id,
            key=S3_INDEX_FILE_NAME,
            content=html_content,
            content_type="text/html"
        )

        TerraformOutput(self, "website_index_url",
                        value = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{S3_INDEX_FILE_NAME}"
        )


app = App()
StaticWebsite(app, "cdktf-python-static-website")

app.synth()