# Take-home 2 — API de reserva de salas (tempo-alvo: 3 h)

Construa uma API HTTP (FastAPI **ou** Django/DRF, à sua escolha) para reservar salas de reunião.

- `POST /salas` `{nome, capacidade}` e `GET /salas`.
- `POST /reservas` `{sala_id, inicio, fim, responsavel}` (datas ISO 8601 com fuso). **Regras:** `fim > inicio`; duração máxima 4 h; não pode começar no passado; **não pode haver sobreposição** na mesma sala (encostar é permitido: uma termina às 10:00, outra começa às 10:00). Conflito → `409`.
- `GET /reservas?sala_id=&data=AAAA-MM-DD` ordenadas por início.
- `DELETE /reservas/{id}` (`204`; inexistente `404`).
- Duas requisições **simultâneas** pelo mesmo horário: no máximo uma pode vencer.
- Testes automatizados, README com decisões e limitações, e uma estratégia explicada para autenticação (não precisa implementar).
