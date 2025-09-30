#!/usr/bin/env python3
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import aws_cdk as cdk

from infra.eks_scheduler_stack import EksSchedulerStack


app = cdk.App()

account = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION", "us-east-1")

EksSchedulerStack(app, "EksSchedulerStack", env=cdk.Environment(account=account, region=region))

app.synth()
