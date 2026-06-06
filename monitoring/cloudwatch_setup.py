"""
Run this script ONCE to create all CloudWatch dashboards and alarms.
Prerequisites: aws configure (with access key that has CloudWatch permissions)

Usage:
  python monitoring/cloudwatch_setup.py --alb-arn <your-alb-arn> --email shadrack.n159@gmail.com
"""

import boto3
import json
import argparse
import sys

REGION = "us-east-1"
SNS_TOPIC_NAME = "pune-api-alerts"
DASHBOARD_NAME = "PuneRealEstateAPI"


def get_or_create_sns_topic(sns, email: str) -> str:
    topic = sns.create_topic(Name=SNS_TOPIC_NAME)
    arn = topic["TopicArn"]
    sns.subscribe(TopicArn=arn, Protocol="email", Endpoint=email)
    print(f"SNS topic: {arn}")
    print(f"Check {email} inbox and confirm the subscription.")
    return arn


def create_alarms(cw, sns_arn: str, alb_arn: str):
    alb_suffix = alb_arn.split("loadbalancer/")[-1] if alb_arn else ""

    alarms = [
        {
            "AlarmName": "pune-api-5xx-error-rate",
            "AlarmDescription": "API 5xx error rate exceeds 5%",
            "Namespace": "AWS/ApplicationELB",
            "MetricName": "HTTPCode_Target_5XX_Count",
            "Dimensions": [{"Name": "LoadBalancer", "Value": alb_suffix}],
            "Statistic": "Sum",
            "Period": 300,
            "EvaluationPeriods": 2,
            "Threshold": 10,
            "ComparisonOperator": "GreaterThanThreshold",
            "AlarmActions": [sns_arn],
            "TreatMissingData": "notBreaching",
        },
        {
            "AlarmName": "pune-api-high-latency",
            "AlarmDescription": "API P99 response time > 2 seconds",
            "Namespace": "AWS/ApplicationELB",
            "MetricName": "TargetResponseTime",
            "Dimensions": [{"Name": "LoadBalancer", "Value": alb_suffix}],
            "ExtendedStatistic": "p99",
            "Period": 300,
            "EvaluationPeriods": 2,
            "Threshold": 2.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "AlarmActions": [sns_arn],
            "TreatMissingData": "notBreaching",
        },
        {
            "AlarmName": "pune-api-unhealthy-hosts",
            "AlarmDescription": "No healthy hosts in target group",
            "Namespace": "AWS/ApplicationELB",
            "MetricName": "HealthyHostCount",
            "Dimensions": [{"Name": "LoadBalancer", "Value": alb_suffix}],
            "Statistic": "Minimum",
            "Period": 60,
            "EvaluationPeriods": 2,
            "Threshold": 1,
            "ComparisonOperator": "LessThanThreshold",
            "AlarmActions": [sns_arn],
            "TreatMissingData": "breaching",
        },
    ]

    for alarm in alarms:
        try:
            cw.put_metric_alarm(**alarm)
            print(f"Alarm created: {alarm['AlarmName']}")
        except Exception as e:
            print(f"Failed to create alarm {alarm['AlarmName']}: {e}")


def create_dashboard(cw, alb_arn: str):
    alb_suffix = alb_arn.split("loadbalancer/")[-1] if alb_arn else "app/pune-api-alb/REPLACE"

    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0, "y": 0, "width": 12, "height": 6,
                "properties": {
                    "title": "Request Count (per 5 min)",
                    "metrics": [["AWS/ApplicationELB", "RequestCount",
                                  "LoadBalancer", alb_suffix]],
                    "period": 300,
                    "stat": "Sum",
                    "view": "timeSeries",
                    "region": REGION,
                }
            },
            {
                "type": "metric",
                "x": 12, "y": 0, "width": 12, "height": 6,
                "properties": {
                    "title": "5xx Error Rate",
                    "metrics": [
                        ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count",
                         "LoadBalancer", alb_suffix, {"label": "5xx errors"}],
                        ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count",
                         "LoadBalancer", alb_suffix, {"label": "4xx errors"}],
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "view": "timeSeries",
                    "region": REGION,
                }
            },
            {
                "type": "metric",
                "x": 0, "y": 6, "width": 12, "height": 6,
                "properties": {
                    "title": "Response Time (P50 / P95 / P99)",
                    "metrics": [
                        ["AWS/ApplicationELB", "TargetResponseTime",
                         "LoadBalancer", alb_suffix,
                         {"stat": "p50", "label": "p50"}],
                        ["AWS/ApplicationELB", "TargetResponseTime",
                         "LoadBalancer", alb_suffix,
                         {"stat": "p95", "label": "p95"}],
                        ["AWS/ApplicationELB", "TargetResponseTime",
                         "LoadBalancer", alb_suffix,
                         {"stat": "p99", "label": "p99"}],
                    ],
                    "period": 300,
                    "view": "timeSeries",
                    "region": REGION,
                }
            },
            {
                "type": "metric",
                "x": 12, "y": 6, "width": 12, "height": 6,
                "properties": {
                    "title": "Healthy Host Count",
                    "metrics": [["AWS/ApplicationELB", "HealthyHostCount",
                                  "LoadBalancer", alb_suffix]],
                    "period": 60,
                    "stat": "Minimum",
                    "view": "timeSeries",
                    "region": REGION,
                }
            },
        ]
    }

    cw.put_dashboard(
        DashboardName=DASHBOARD_NAME,
        DashboardBody=json.dumps(dashboard_body),
    )
    print(f"Dashboard created: {DASHBOARD_NAME}")
    print(f"View at: https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")


def main():
    parser = argparse.ArgumentParser(description="Set up CloudWatch monitoring")
    parser.add_argument("--alb-arn", required=True, help="ARN of the Application Load Balancer")
    parser.add_argument("--email", default="shadrack.n159@gmail.com", help="Alert email address")
    args = parser.parse_args()

    session = boto3.Session(region_name=REGION)
    sns = session.client("sns")
    cw = session.client("cloudwatch")

    print("=== Setting up CloudWatch monitoring ===")
    sns_arn = get_or_create_sns_topic(sns, args.email)
    create_alarms(cw, sns_arn, args.alb_arn)
    create_dashboard(cw, args.alb_arn)
    print("\n=== Done. Confirm email subscription before alarms can notify you. ===")


if __name__ == "__main__":
    main()
