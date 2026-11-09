{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MidiaDoMiniShop",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::__BUCKET__/products/*"
    },
    {
      "Sid": "ListarSoOPrefixoProducts",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::__BUCKET__",
      "Condition": { "StringLike": { "s3:prefix": "products/*" } }
    },
    {
      "Sid": "LerSegredosDoMiniShop",
      "Effect": "Allow",
      "Action": ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
      "Resource": "arn:aws:ssm:*:*:parameter/minishop/*"
    },
    {
      "Sid": "EscreverLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:log-group:/minishop/*:*"
    },
    {
      "Sid": "BaixarAImagem",
      "Effect": "Allow",
      "Action": ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"],
      "Resource": "arn:aws:ecr:*:*:repository/minishop"
    },
    {
      "Sid": "LoginNoECR",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    }
  ]
}
