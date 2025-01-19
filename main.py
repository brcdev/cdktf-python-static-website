#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_object import S3Object
from cdktf_cdktf_provider_aws.s3_bucket_public_access_block import S3BucketPublicAccessBlock
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.s3_bucket_versioning import S3BucketVersioningA, S3BucketVersioningVersioningConfiguration
from cdktf_cdktf_provider_aws.cloudfront_distribution import CloudfrontDistribution, CloudfrontDistributionRestrictions, CloudfrontDistributionRestrictionsGeoRestriction, CloudfrontDistributionViewerCertificate, CloudfrontDistributionDefaultCacheBehavior, CloudfrontDistributionOrigin,  CloudfrontDistributionDefaultCacheBehaviorForwardedValues, CloudfrontDistributionDefaultCacheBehaviorForwardedValuesCookies
from cdktf_cdktf_provider_aws.cloudfront_origin_access_control import CloudfrontOriginAccessControl
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
import time

AWS_REGION="eu-central-1"
S3_BUCKET_NAME="cdk-python-static-website-demo"
S3_INDEX_FILE_NAME="index.html"
S3_ORIGIN_ID="static-website-s3-origin"

class StaticWebsite(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # Configure AWS provider
        AwsProvider(self, "AWS", region=AWS_REGION)
        caller_identity = DataAwsCallerIdentity(self, "CallerIdentity")

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

        # Block public access to S3 bucket
        S3BucketPublicAccessBlock(self, "block",
            bucket=website_bucket.id,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True,
            restrict_public_buckets=True
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

        website_oac = CloudfrontOriginAccessControl(self, "website_oac",
            name="website_oac",
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4"
        )

        cloudfront_distribution = CloudfrontDistribution(self, "website_distribution",
            default_cache_behavior=CloudfrontDistributionDefaultCacheBehavior(
                allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"
                ],
                cached_methods=["GET", "HEAD"],
                default_ttl=3600,
                forwarded_values=CloudfrontDistributionDefaultCacheBehaviorForwardedValues(
                    cookies=CloudfrontDistributionDefaultCacheBehaviorForwardedValuesCookies(
                        forward="none"
                    ),
                    query_string=False
                ),
                max_ttl=86400,
                min_ttl=0,
                target_origin_id=S3_ORIGIN_ID,
                viewer_protocol_policy="https-only"
            ),
            default_root_object=S3_INDEX_FILE_NAME,
            enabled=True,
            origin=[CloudfrontDistributionOrigin(
                domain_name=website_bucket.bucket_regional_domain_name,
                origin_access_control_id=website_oac.id,
                origin_id=S3_ORIGIN_ID
            )
            ],
            restrictions=CloudfrontDistributionRestrictions(
                geo_restriction=CloudfrontDistributionRestrictionsGeoRestriction(
                    locations=[],
                    restriction_type="none"
                )
            ),
            viewer_certificate=CloudfrontDistributionViewerCertificate(
                cloudfront_default_certificate=True
            )
        )

        # Configure bucket policy for CloudFront
        S3BucketPolicy(self, "allow_cloudfront_only",
            bucket=website_bucket.id,
            policy=f'''
            {{
                "Version": "2012-10-17",
                "Statement": {{
                    "Sid": "AllowCloudFrontServicePrincipalReadOnly",
                    "Effect": "Allow",
                    "Principal": {{
                        "Service": "cloudfront.amazonaws.com"
                    }},
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::{website_bucket.id}/*",
                    "Condition": {{
                        "StringEquals": {{
                            "AWS:SourceArn": "arn:aws:cloudfront::{caller_identity.account_id}:distribution/{cloudfront_distribution.id}"
                        }}
                    }}
                }}
            }}
            '''
        )

        TerraformOutput(self, "cloudfront_distribution_domain",
                        value = cloudfront_distribution.domain_name
        )


app = App()
StaticWebsite(app, "cdktf-python-static-website")

app.synth()