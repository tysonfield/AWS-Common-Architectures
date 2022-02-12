#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.cdk_stack import CdkStack


app = cdk.App()
test_env = cdk.Environment(region = "ap-southeast-2")
CdkStack(app, "cdk", env=test_env)

app.synth()
