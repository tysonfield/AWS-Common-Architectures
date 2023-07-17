#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.three_tier_simple import ThreeTierSimple


app = cdk.App()
test_env = cdk.Environment(region = "ap-southeast-2")
ThreeTierSimple(app, "my-app", env=test_env)

app.synth()
