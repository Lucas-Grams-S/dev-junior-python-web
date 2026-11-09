# Configuração comum dos scripts da aula 13 (fazer `source`, não executar).
# Tudo que o curso cria na AWS recebe a tag Project=$PROJECT_TAG: é por ela que a destruição e a conferência acham os recursos.
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-sa-east-1}"   # São Paulo: menor latência; confira preços da região
export AWS_PAGER=""                                            # a CLI não abre o `less`
export PROJECT_TAG="minishop-curso"
export NAME="minishop"
export BUCKET="${NAME}-midia-$(aws sts get-caller-identity --query Account --output text)"   # nomes de bucket são GLOBAIS: o ID da conta evita colisão
export DB_ID="${NAME}-db"
export INSTANCE_TYPE="${INSTANCE_TYPE:-t3.micro}"              # CONFIRA se é elegível ao seu plano (aula 13.01)
export DB_CLASS="${DB_CLASS:-db.t4g.micro}"
export DB_ENGINE_VERSION="${DB_ENGINE_VERSION:-}"              # vazio = a CLI escolhe a padrão; veja `aws rds describe-db-engine-versions`
export TAGS_KV="Key=Project,Value=${PROJECT_TAG}"
export TAGS_SPEC_JSON="[{\"Key\":\"Project\",\"Value\":\"${PROJECT_TAG}\"}]"
