variable "access_key" {}
variable "secret_key" {}
variable "bucket_name" {}
# This will be used to identify twarc-cloud related resources.
variable "env_name" {
  default = "twarc-cloud"
}

variable "region" {
  default = "us-east-1"
}

variable "az" {
  default = "a"
}