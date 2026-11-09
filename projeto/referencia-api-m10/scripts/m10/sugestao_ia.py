"""Sugestão TÍPICA de um assistente de IA para 'aplicar cupom' (escrita por mim, para a aula, imitando padrões comuns): parece razoável, compila e roda."""
import sqlite3


def aplicar_cupom(total: float, cupom: str, caminho_do_banco: str = "db.sqlite3") -> float:
    try:
        conexao = sqlite3.connect(caminho_do_banco)
        linha = conexao.execute(f"SELECT percentual FROM cupons WHERE codigo = '{cupom}'").fetchone()
        desconto = total * linha[0] / 100
        return round(total - desconto, 2)
    except:
        return total
