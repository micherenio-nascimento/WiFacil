# Instalação do WiFácil Turbo

## Copiar o projeto

Pelo Ubuntu, com o SSH USB funcionando:

```bash
scp -r src termux-a01:/data/data/com.termux/files/home/wifacil-turbo
ssh termux-a01
cd ~/wifacil-turbo
```

## Configurar

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Use uma senha exclusiva com pelo menos 10 caracteres:

```dotenv
WIFACIL_ADMIN_PASSWORD=uma-senha-longa-e-exclusiva
```

A senha só é usada quando o banco é criado. Ela é convertida em PBKDF2 com salt;
o valor em texto puro não é gravado no SQLite.

Edite `config.json` para alterar marca, Pix e planos. Valores monetários usam
centavos para evitar arredondamento:

```json
{"id":"economico","name":"Econômico","price_cents":200,"minutes":120,"data_mb":1024}
```

Enquanto estiver testando, mantenha:

```json
"firewall_enabled": false
```

## Permissões e inicialização

```bash
chmod 700 start.sh stop.sh firewall.sh
./start.sh
```

Verifique:

```bash
tail -f data/server.log
```

Pare com:

```bash
./stop.sh
```

## Testar pelo Ubuntu

```bash
adb forward tcp:8080 tcp:8080
curl -I http://127.0.0.1:8080/
```

Abra:

```text
http://127.0.0.1:8080/
http://127.0.0.1:8080/admin
```

## Banco e arquivos gerados

O diretório `data/` contém:

```text
wifacil.db
wifacil.db-wal
wifacil.db-shm
session.secret
server.pid
server.log
```

Não versione nem publique esse diretório. Para backup consistente, pare o serviço
antes de copiar o banco.
