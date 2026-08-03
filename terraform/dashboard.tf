# CloudWatch dashboard built entirely from metrics AWS publishes for free
# (ECS service CPU/Memory, HTTP API Gateway, autoscaling alarms) — no
# Container Insights, so no added per-metric cost.
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "aws-fargate-demo"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS CPU Utilization"
          view   = "timeSeries"
          region = "us-east-1"
          period = 60
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.app.name, { stat = "Average", label = "Avg CPU %" }],
            ["...", { stat = "Maximum", label = "Max CPU %" }],
          ]
          annotations = {
            horizontal = [{ label = "Autoscaling target (70%)", value = 70 }]
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Memory Utilization"
          view   = "timeSeries"
          region = "us-east-1"
          period = 60
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.app.name, { stat = "Average", label = "Avg Memory %" }],
            ["...", { stat = "Maximum", label = "Max Memory %" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "API Requests & Errors"
          view   = "timeSeries"
          region = "us-east-1"
          period = 60
          stat   = "Sum"
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.main.id, { label = "Requests" }],
            ["AWS/ApiGateway", "4xxError", "ApiId", aws_apigatewayv2_api.main.id, { label = "4xx Errors" }],
            ["AWS/ApiGateway", "5xxError", "ApiId", aws_apigatewayv2_api.main.id, { label = "5xx Errors" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "API Latency (ms)"
          view   = "timeSeries"
          region = "us-east-1"
          period = 60
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiId", aws_apigatewayv2_api.main.id, { stat = "Average", label = "Avg Latency" }],
            ["AWS/ApiGateway", "Latency", "ApiId", aws_apigatewayv2_api.main.id, { stat = "p99", label = "p99 Latency" }],
            ["AWS/ApiGateway", "IntegrationLatency", "ApiId", aws_apigatewayv2_api.main.id, { stat = "Average", label = "Avg Integration Latency" }],
          ]
        }
      },
      {
        type   = "alarm"
        x      = 0
        y      = 12
        width  = 24
        height = 4
        properties = {
          title  = "Autoscaling Alarms (CPU target-tracking)"
          alarms = aws_appautoscaling_policy.ecs_cpu.alarm_arns
        }
      },
    ]
  })
}

output "dashboard_url" {
  value = "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
