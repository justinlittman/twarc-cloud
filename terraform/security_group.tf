# Security Group for container
resource "aws_security_group" "container" {
  vpc_id      = "${module.vpc.vpc_id}"
  name        = "${var.env_name}-ecs-container-sg"
  description = "Allow egress from container"
}

resource "aws_security_group_rule" "container_egress" {
  type        = "egress"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = "${aws_security_group.container.id}"
}

resource "aws_security_group_rule" "container_ingress" {
  type                     = "ingress"
  from_port                = "80"
  to_port                  = "80"
  protocol                 = "tcp"
  cidr_blocks              = ["0.0.0.0/0"]
  security_group_id        = "${aws_security_group.container.id}"
}

output "security_group_id" {
  value = "${aws_security_group.container.id}"
}
