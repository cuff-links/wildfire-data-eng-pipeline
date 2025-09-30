from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import assertions

from infra.eks_scheduler_stack import EksSchedulerStack


def synth_template(**stack_kwargs) -> assertions.Template:
    app = cdk.App()
    stack = EksSchedulerStack(app, "TestEksSchedulerStack", **stack_kwargs)
    return assertions.Template.from_stack(stack)


def test_cluster_and_nodegroup_created() -> None:
    template = synth_template()

    template.resource_count_is("AWS::EKS::Cluster", 1)

    template.has_resource_properties(
        "AWS::EKS::Nodegroup",
        assertions.Match.object_like(
            {
                "ScalingConfig": {
                    "DesiredSize": 0,
                    "MaxSize": 4,
                    "MinSize": 0,
                }
            }
        ),
    )


def test_scaler_lambda_environment_and_role() -> None:
    template = synth_template(max_node_capacity=6)

    template.has_resource_properties(
        "AWS::Lambda::Function",
        assertions.Match.object_like(
            {
                "Environment": {
                    "Variables": assertions.Match.object_like(
                        {
                            "CLUSTER_NAME": assertions.Match.any_value(),
                            "NODEGROUP_NAME": assertions.Match.any_value(),
                            "MAX_CAPACITY": "6",
                        }
                    )
                }
            }
        ),
    )

    template.has_resource_properties(
        "AWS::IAM::Policy",
        assertions.Match.object_like(
            {
                "PolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": [
                                            "eks:DescribeNodegroup",
                                            "eks:UpdateNodegroupConfig",
                                        ]
                                    }
                                )
                            ]
                        )
                    }
                )
            }
        ),
    )


def test_scheduler_schedules_timezone_and_payload() -> None:
    template = synth_template(start_desired_capacity=3, start_min_capacity=2)

    template.has_resource_properties(
        "AWS::Scheduler::Schedule",
        assertions.Match.object_like(
            {
                "ScheduleExpression": "cron(0 9 * * ? *)",
                "ScheduleExpressionTimezone": "America/New_York",
                "Target": assertions.Match.object_like(
                    {
                        "Arn": assertions.Match.object_like(
                            {
                                "Fn::GetAtt": assertions.Match.array_with(
                                    [
                                        assertions.Match.string_like_regexp(
                                            "NodegroupScalerFn.*"
                                        ),
                                        "Arn",
                                    ]
                                )
                            }
                        ),
                        "RoleArn": assertions.Match.object_like(
                            {
                                "Fn::GetAtt": assertions.Match.array_with(
                                    [
                                        assertions.Match.string_like_regexp(
                                            "SchedulerInvokeRole.*"
                                        ),
                                        "Arn",
                                    ]
                                )
                            }
                        ),
                        "Input": assertions.Match.serialized_json(
                            {
                                "desiredCapacity": 3,
                                "minCapacity": 2,
                            }
                        ),
                    }
                ),
            }
        ),
    )

    template.has_resource_properties(
        "AWS::Scheduler::Schedule",
        assertions.Match.object_like(
            {
                "ScheduleExpression": "cron(0 21 * * ? *)",
                "ScheduleExpressionTimezone": "America/New_York",
                "Target": assertions.Match.object_like(
                    {
                        "Input": assertions.Match.serialized_json(
                            {
                                "desiredCapacity": 0,
                                "minCapacity": 0,
                            }
                        )
                    }
                ),
            }
        ),
    )


def test_stack_outputs_present() -> None:
    template = synth_template()

    template.has_output(
        "ClusterName",
        assertions.Match.object_like(
            {"Value": assertions.Match.any_value()}
        ),
    )
    template.has_output(
        "NodegroupName",
        assertions.Match.object_like(
            {"Value": assertions.Match.any_value()}
        ),
    )
    template.has_output(
        "UpdateKubeconfigCmd",
        assertions.Match.object_like(
            {
                "Value": assertions.Match.string_like_regexp(
                    r"aws eks update-kubeconfig --name .+ --region .+"
                )
            }
        ),
    )
