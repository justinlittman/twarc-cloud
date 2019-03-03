# Cloudwatch Log Group for ECS
resource "aws_cloudwatch_log_group" "cluster" {
  name = "${var.env_name}-container"
  retention_in_days = "14"
}

output "log_group" {
  value = "${aws_cloudwatch_log_group.cluster.name}"
}
