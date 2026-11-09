"""O SERVIDOR recusa TLS antigo? O cliente OpenSSL moderno nem oferece TLS 1.0/1.1 por padrão; aqui rebaixamos o nível de segurança
do CLIENTE (só neste teste, contra o nosso servidor local) para realmente tentar versões velhas."""
import socket, ssl, sys
PORTA = int(sys.argv[1])
for nome, versao in [("TLS 1.0", ssl.TLSVersion.TLSv1), ("TLS 1.1", ssl.TLSVersion.TLSv1_1), ("TLS 1.2", ssl.TLSVersion.TLSv1_2), ("TLS 1.3", ssl.TLSVersion.TLSv1_3)]:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(sys.argv[2])
    try:
        ctx.set_ciphers("ALL:@SECLEVEL=0")
        ctx.minimum_version = ctx.maximum_version = versao
    except (ssl.SSLError, ValueError) as e:
        print(f"   {nome}: cliente não consegue nem tentar ({e.__class__.__name__})"); continue
    try:
        with socket.create_connection(("127.0.0.1", PORTA), timeout=5) as s, ctx.wrap_socket(s, server_hostname="localhost") as t:
            print(f"   {nome}: ACEITO pelo servidor ({t.version()}, {t.cipher()[0]})")
    except (ssl.SSLError, OSError) as e:
        print(f"   {nome}: recusado pelo servidor ({str(e)[:70]})")
