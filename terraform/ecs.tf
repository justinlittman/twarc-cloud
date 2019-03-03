# ECS
resource "aws_ecs_cluster" "cluster" {
  name = "${var.env_name}-cluster"
}

output "cluster_name" {
  value = "${aws_ecs_cluster.cluster.name}"
}
