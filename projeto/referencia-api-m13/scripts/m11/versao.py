import sys

match sys.version_info[:2]:
    case (3, 13):
        print("rodando no Python 3.13: ok")
    case _:
        print("outra versão")
