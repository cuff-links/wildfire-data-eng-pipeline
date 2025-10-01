from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_scheduler as scheduler,
)
from constructs import Construct


class EksSchedulerStack(Stack):
    """Provision an EKS cluster with managed workers and scheduled scaling."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        max_node_capacity: int = 4,
        start_desired_capacity: int = 2,
        start_min_capacity: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "EksVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", cidr_mask=24, subnet_type=ec2.SubnetType.PUBLIC
                ),
                ec2.SubnetConfiguration(
                    name="Private", cidr_mask=24, subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
            ],
        )

        cluster_name = "AstronomerEksCluster"

        cluster_role = iam.Role(
            self,
            "EksClusterRole",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            description="Service role assumed by the EKS control plane",
        )
        cluster_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy")
        )

        cluster_security_group = ec2.SecurityGroup(
            self,
            "EksControlPlaneSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group associated with the EKS control plane",
        )

        private_subnet_ids = [subnet.subnet_id for subnet in vpc.private_subnets]

        cluster = eks.CfnCluster(
            self,
            "AstronomerEksCluster",
            name=cluster_name,
            version="1.34",
            role_arn=cluster_role.role_arn,
            resources_vpc_config=eks.CfnCluster.ResourcesVpcConfigProperty(
                endpoint_private_access=True,
                endpoint_public_access=True,
                security_group_ids=[cluster_security_group.security_group_id],
                subnet_ids=private_subnet_ids,
            ),
        )

        node_role = iam.Role(
            self,
            "EksNodegroupRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Role assumed by EKS managed worker nodes",
        )
        node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy")
        )
        node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy")
        )
        node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonEC2ContainerRegistryReadOnly"
            )
        )

        nodegroup = eks.CfnNodegroup(
            self,
            "AstronomerWorkers",
            cluster_name=cluster_name,
            node_role=node_role.role_arn,
            subnets=private_subnet_ids,
            scaling_config=eks.CfnNodegroup.ScalingConfigProperty(
                desired_size=0,
                max_size=max_node_capacity,
                min_size=0,
            ),
            instance_types=["t3.medium"],
            ami_type="AL2023_x86_64_STANDARD",
            disk_size=80,
        )
        nodegroup.node.add_dependency(cluster)

        scaler_role = iam.Role(
            self,
            "NodegroupScalerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role assumed by scheduled Lambda to adjust nodegroup capacity",
        )
        scaler_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )
        scaler_role.add_to_policy(
            iam.PolicyStatement(
                actions=["eks:DescribeNodegroup", "eks:UpdateNodegroupConfig"],
                resources=[nodegroup.attr_arn],
            )
        )

        lambda_asset_path = Path(__file__).resolve().parent / "lambda" / "scale_nodegroup"

        scaler_function = lambda_.Function(
            self,
            "NodegroupScalerFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.on_event",
            code=lambda_.Code.from_asset(str(lambda_asset_path)),
            role=scaler_role,
            timeout=cdk.Duration.seconds(120),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
            environment={
                "CLUSTER_NAME": cluster_name,
                "NODEGROUP_NAME": nodegroup.attr_nodegroup_name,
                "MAX_CAPACITY": str(max_node_capacity),
            },
        )

        start_payload: Dict[str, Any] = {
            "desiredCapacity": start_desired_capacity,
            "minCapacity": start_min_capacity,
        }
        stop_payload: Dict[str, Any] = {
            "desiredCapacity": 0,
            "minCapacity": 0,
        }

        scheduler_role = iam.Role(
            self,
            "SchedulerInvokeRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
            description="Role assumed by EventBridge Scheduler to invoke the scaler Lambda",
        )
        scaler_function.grant_invoke(scheduler_role)

        def schedule_id(suffix: str) -> str:
            return f"AstronomerWorkers{suffix}"

        scheduler.CfnSchedule(
            self,
            schedule_id("StartSchedule"),
            description="Scale EKS nodegroup up at 9AM Eastern",
            schedule_expression="cron(0 9 * * ? *)",
            schedule_expression_timezone="America/New_York",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=scaler_function.function_arn,
                role_arn=scheduler_role.role_arn,
                input=json.dumps(start_payload),
            ),
        )

        scheduler.CfnSchedule(
            self,
            schedule_id("StopSchedule"),
            description="Scale EKS nodegroup down at 9PM Eastern",
            schedule_expression="cron(0 21 * * ? *)",
            schedule_expression_timezone="America/New_York",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=scaler_function.function_arn,
                role_arn=scheduler_role.role_arn,
                input=json.dumps(stop_payload),
            ),
        )

        region_placeholder = "${AWS::Region}"

        cdk.CfnOutput(
            self,
            "ClusterName",
            value=cluster_name,
            export_name=f"{self.stack_name}:ClusterName",
        )
        cdk.CfnOutput(
            self,
            "NodegroupName",
            value=nodegroup.attr_nodegroup_name,
            export_name=f"{self.stack_name}:NodegroupName",
        )
        cdk.CfnOutput(
            self,
            "UpdateKubeconfigCmd",
            value=(
                f"aws eks update-kubeconfig --name {cluster_name} "
                f"--region {region_placeholder}"
            ),
        )
