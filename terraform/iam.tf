# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.env_name}-ecs-task-execution-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy_attach" {
  role       = "${aws_iam_role.ecs_execution_role.id}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

output "execution_role_arn" {
  value = "${aws_iam_role.ecs_execution_role.arn}"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.env_name}-ecs-task-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "ecs_task_s3_policy" {
  name        = "${var.env_name}-s3-ecs-task-policy"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_task_s3_policy_attach" {
  role       = "${aws_iam_role.ecs_task_role.id}"
  policy_arn = "${aws_iam_policy.ecs_task_s3_policy.arn}"
}

output "task_role_arn" {
  value = "${aws_iam_role.ecs_task_role.arn}"
}


# Cloudwatch Events Role
resource "aws_iam_role" "event_role" {
  name = "${var.env_name}-event-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "event_role_policy_attach" {
  role       = "${aws_iam_role.event_role.id}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceEventsRole"
}

output "event_role_arn" {
  value = "${aws_iam_role.event_role.arn}"
}

# User
resource "aws_iam_user" "user" {
  name = "${var.env_name}-user"
}

resource "aws_iam_access_key" "user" {
  user = "${aws_iam_user.user.name}"
}

output "access_key" {
  value = "${aws_iam_access_key.user.id}"
}

output "secret_key" {
  value = "${aws_iam_access_key.user.secret}"
}

resource "aws_iam_user_policy_attachment" "user_s3_policy_attach" {
  user       = "${aws_iam_user.user.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_user_policy_attachment" "user_ecs_policy_attach" {
  user       = "${aws_iam_user.user.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_user_policy_attachment" "user_cloudwatch_events_policy_attach" {
  user       = "${aws_iam_user.user.name}"
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
}

resource "aws_iam_policy" "user_iam_policy" {
  name        = "${var.env_name}-user-iam-policy"
  policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}


resource "aws_iam_user_policy_attachment" "user_iam_policy_attach" {
  user       = "${aws_iam_user.user.name}"
  policy_arn = "${aws_iam_policy.user_iam_policy.arn}"
}
