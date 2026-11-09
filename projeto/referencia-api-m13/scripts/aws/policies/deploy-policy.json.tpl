{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnviarImagem",
      "Effect": "Allow",
      "Action": ["ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage"],
      "Resource": "arn:aws:ecr:*:__ACCOUNT__:repository/minishop"
    },
    { "Sid": "LoginNoECR", "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" },
    {
      "Sid": "AcharAInstancia",
      "Effect": "Allow",
      "Action": "ec2:DescribeInstances",
      "Resource": "*"
    },
    {
      "Sid": "MandarComandoSoParaAInstanciaDoProjeto",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ec2:*:__ACCOUNT__:instance/*",
      "Condition": { "StringEquals": { "ssm:resourceTag/Project": "minishop-curso" } }
    },
    {
      "Sid": "DocumentoDeComando",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ssm:*::document/AWS-RunShellScript"
    },
    {
      "Sid": "AcompanharComando",
      "Effect": "Allow",
      "Action": ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"],
      "Resource": "*"
    }
  ]
}
