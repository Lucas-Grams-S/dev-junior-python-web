# Uso de IA no MiniShop

Regras do projeto para usar assistentes de IA (em vez de cada pessoa decidir sozinha).

## Pode
- Rascunhar código, testes, scripts e documentação; explicar erros e código; sugerir alternativas e refatorações.
- Pedir revisão de um trecho **sem dados reais** (use exemplos sintéticos).

## Não pode
- Compartilhar **segredos** (`.env`, chaves, tokens, senhas), **dados pessoais** de clientes ou dados de produção. Descreva a configuração só com os **nomes** das variáveis.
- Commitar código que você **não consegue explicar**.
- Instalar um pacote só porque uma IA o citou.

## Como verificar antes de aceitar
1. **Critérios e testes primeiro:** escreva (ou peça) os testes do requisito antes de aceitar a implementação.
2. **Portões automáticos:** `bash scripts/definicao_de_pronto.sh`.
3. **Leitura humana:** regra de negócio, tratamento de erro (nada de `except` engolindo erro), segurança (entrada do usuário vai para SQL/HTML/CSV/log?), dinheiro em `Decimal`.
4. **Dependências:** o pacote existe no PyPI? Histórico, mantenedores e repositório? `pip-audit` limpo?
5. **APIs:** a função/parâmetro existe na versão fixada? Confira na documentação oficial.

## Transparência
Se um trecho relevante foi gerado ou muito assistido, diga no PR (campo "riscos e pontos de atenção"). Quem abre o PR responde pelo código, tenha vindo de onde vier.

## Se algo vazou
Trate como incidente: avise o time, **rotacione** o segredo, avalie dados pessoais (LGPD) e registre o aprendizado.
