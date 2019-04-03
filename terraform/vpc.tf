# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.env_name}--vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}${var.az}"]
  private_subnets = ["10.0.1.0/24"]
  public_subnets  = ["10.0.101.0/24"]

  enable_vpn_gateway = true
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = ["${module.vpc.public_subnets}"]
}
