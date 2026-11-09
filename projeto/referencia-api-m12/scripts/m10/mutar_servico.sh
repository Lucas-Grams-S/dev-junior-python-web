# Mutantes no caso de uso `create_order`; rodamos os 3 estilos de teste contra cada um.
F=apps/orders/services.py; cp $F /tmp/services.orig
roda() { printf "%-34s" "$1"; uv run pytest -q tests/test_mocks_vs_fakes.py -p no:randomly -p no:cacheprovider 2>&1 | grep -E "^FAILED" | sed 's/.*::test_//; s/ - .*//' | tr '\n' ' '; echo; }
echo "estilos: estado_com_fake | mock_sequencia_exata | mock_so_o_essencial"
roda "0) código original (nenhuma falha)"
python3 - <<'PY'
s=open("apps/orders/services.py").read()
s=s.replace("        for linha in linhas:\n            if not repo.baixar_estoque(linha.product_id, linha.quantidade):   # defesa extra: nunca deveria ocorrer com a trava\n                raise StockError(f\"{linha.nome}: o estoque mudou, tente novamente.\")\n        repo.esvaziar_carrinho(carrinho)",
"        repo.esvaziar_carrinho(carrinho)\n        for linha in linhas:\n            if not repo.baixar_estoque(linha.product_id, linha.quantidade):   # defesa extra: nunca deveria ocorrer com a trava\n                raise StockError(f\"{linha.nome}: o estoque mudou, tente novamente.\")")
open("apps/orders/services.py","w").write(s)
PY
roda "1) REFATORAÇÃO inofensiva (ordem)"
cp /tmp/services.orig $F
python3 - <<'PY'
s=open("apps/orders/services.py").read()
s=s.replace("        for linha in linhas:\n            if not repo.baixar_estoque(linha.product_id, linha.quantidade):   # defesa extra: nunca deveria ocorrer com a trava\n                raise StockError(f\"{linha.nome}: o estoque mudou, tente novamente.\")\n","")
open("apps/orders/services.py","w").write(s)
PY
roda "2) BUG REAL: não baixa o estoque"
cp /tmp/services.orig $F
python3 - <<'PY'
s=open("apps/orders/services.py").read()
s=s.replace("        repo.esvaziar_carrinho(carrinho)\n","")
open("apps/orders/services.py","w").write(s)
PY
roda "3) BUG REAL: não esvazia o carrinho"
cp /tmp/services.orig $F
roda "restaurado"
