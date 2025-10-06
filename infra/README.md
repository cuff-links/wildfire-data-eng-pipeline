# Wildfire Infra

## Prerequisites
- Python 3.10+
- AWS credentials with permissions for VPC, IAM, EKS, Lambda, EventBridge
- CDK bootstrap completed in the target account/region

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap aws://ACCOUNT/REGION
pytest  # optional: run assertions against the synthesized template
```

## Deploy the EKS scheduler stack
```bash
cdk synth
cdk deploy
```

### What gets created
- VPC with public and private subnets for the cluster
- EKS cluster (v1.33) with a managed spot node group using `t3.small` nodes and the `AL2023_x86_64_STANDARD` AMI
- Lambda function that adjusts node-group capacity
- EventBridge rules that invoke the Lambda at 9am/9pm America/New_York
- AWS Secrets Manager secret earmarked for Astronomer remote execution credentials

### Scheduling behaviour
The node group is scaled to the following capacities:
- 9am ET: `desired=2`, `min=1`, `max=4`
- 9pm ET: `desired=0`, `min=0`, `max=0`

Adjust the defaults by overriding props when instantiating `EksSchedulerStack` in `app.py`, or by editing the values inside the stack. The Lambda honours the `MAX_CAPACITY` environment variable.

### Connecting Astronomer Remote Execution
1. After deployment, configure your kubeconfig:
   ```bash
   aws eks update-kubeconfig --name <cluster> --region <region>
   ```
2. Follow the Astronomer [remote execution agent docs](https://www.astronomer.io/docs/astro/remote-execution-agents) to install the agent into the cluster. Typical steps include:
   - Creating the namespace and Kubernetes secret with your Astronomer API token
   - Applying the provided Helm chart or manifests for the agent
3. Ensure that the agent pods run on the managed node group by matching taints/labels if needed.
4. Store the Astronomer API token in the generated Secrets Manager secret (see the `RemoteExecutionAgentSecretArn` stack output). The worker node IAM role already has read access.

### Tear down
Run `cdk destroy` to remove the stack. This deletes the EKS cluster and supporting infrastructure.

### Testing the CDK app
Run `pytest` inside the `infra/` directory to verify that the stack synthesizes the expected resources (cluster, Lambda, EventBridge schedules, and outputs).
