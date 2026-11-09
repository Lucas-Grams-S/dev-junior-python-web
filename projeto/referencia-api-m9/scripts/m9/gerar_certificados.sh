# Gera a CA e o certificado de LABORATÓRIO (válidos por 2 dias). As chaves NÃO são versionadas (.gitignore).
set -eu
mkdir -p scripts/m9/tls && cd scripts/m9/tls
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.pem -days 2 -subj "/CN=MiniShop Lab CA" 2>/dev/null
openssl req -newkey rsa:2048 -nodes -keyout srv.key -out srv.csr -subj "/CN=localhost" 2>/dev/null
printf "subjectAltName=DNS:localhost,IP:127.0.0.1\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n" > ext.cnf
openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out srv.pem -days 2 -extfile ext.cnf 2>/dev/null
echo "certificados de laboratório gerados em scripts/m9/tls/"
