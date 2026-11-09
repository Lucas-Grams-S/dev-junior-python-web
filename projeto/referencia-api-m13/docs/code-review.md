# Guia de code review

## Para quem revisa
**Ordem de leitura:** (1) a descrição e o *porquê*; (2) os testes (eles dizem o que o autor acha que o código faz); (3) o código.

| Olhe para | Pergunte |
|---|---|
| **Correção** | Faz o que a descrição diz? E nos casos de borda (vazio, zero, fronteira, duplicata, concorrência)? |
| **Segurança** | Quem pode chamar? A autorização é **por objeto**? Entrada do usuário vai para SQL, HTML, CSV, log, comando? Segredos? Dados pessoais? |
| **Testes** | O teste falharia sem a mudança? Verifica resultado ou só executa? Cobre o erro e a fronteira? |
| **Design** | Está na camada certa? Dá para testar sem banco? Há acoplamento novo? Nome claro? Complexidade necessária? |
| **Desempenho** | Consulta dentro de laço (N+1)? Carrega tudo na memória? Índice? |
| **Operação** | Migração segura? Log útil e sem dados sensíveis? Configuração por ambiente? Compatível com o que já roda? |

**Classifique cada comentário:** `bloqueante:` (não entra assim), `sugestão:` (melhoraria, a critério do autor), `dúvida:` (quero entender), `nit:` (detalhe de estilo, opcional). Comente o **código**, não a pessoa; explique o **porquê**; proponha uma saída ou **escreva o teste que prova o problema**. Elogie o que está bom.

## Para quem escreve
PR **pequeno** (idealmente < 400 linhas), uma ideia por PR; descrição que conta o porquê; rode os portões antes; responda a cada comentário (corrigiu, discorda com argumento, ou virou issue); não leve a revisão para o lado pessoal.

## O que a máquina já cobre (não gaste revisão humana com isso)
Formatação, imports, variáveis não usadas, tipos, SQL por concatenação, segredos, cobertura mínima. **Humano revisa:** regra de negócio, segurança de verdade, design, nomes, testes que verificam.
