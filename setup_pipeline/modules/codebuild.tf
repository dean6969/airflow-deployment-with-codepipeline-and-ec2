# Tạo CodeBuild Project
resource "aws_codebuild_project" "my_codebuild_project" {
  name          = "${var.project_name}-codebuild-project-${var.env_name}"
  service_role  = aws_iam_role.codebuild_role.arn
  build_timeout = 5

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
  }

  source {
    type      = "CODEPIPELINE"  # Liên kết với CodePipeline
    buildspec = "buildspec.yml" # Trỏ đến tệp buildspec.yml
  }

  artifacts {
    type = "CODEPIPELINE"
  }
}

# IAM Role cho CodeBuild
resource "aws_iam_role" "codebuild_role" {
  name = "${var.project_name}-codebuild-role-${var.env_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "codebuild.amazonaws.com"
      }
    }]
  })
}

# Gắn chính sách cho CodeBuild để có quyền truy cập vào các dịch vụ AWS
resource "aws_iam_role_policy_attachment" "codebuild_attach" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy" "codebuild_logs_policy" {
  name = "${var.project_name}-codebuild-logs-policy-${var.env_name}"
  role = aws_iam_role.codebuild_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:log-group:/aws/codebuild/*"
      }
    ]
  })
}

# Gắn chính sách cho CodeBuild để có quyền truy cập IAM, Kinesis và Lambda
resource "aws_iam_role_policy_attachment" "codebuild_kinesis_policy_attach" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisFullAccess"
}

resource "aws_iam_role_policy_attachment" "codebuild_policy_attach" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "codebuild_IAM_access" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = "arn:aws:iam::aws:policy/IAMFullAccess"
}

resource "aws_iam_role_policy_attachment" "codebuild_lambda_policy_attach" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}