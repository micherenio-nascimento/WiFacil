# Operação diária

## Ordem de inicialização

1. Ative os dados móveis.
2. Ative o hotspot Wi-Fi.
3. Abra o Termux e inicie `sshd`, se a administração USB for necessária.
4. Execute `~/wifacil-turbo/start.sh`.
5. Confirme o portal antes de habilitar o firewall.

## Aprovar um Pix

1. Entre em `/admin`.
2. Localize a solicitação `pending`.
3. Confira valor e recebimento no aplicativo bancário.
4. Clique em **Aprovar** ou **Recusar**.

Ao aprovar, uma sessão é criada com a duração do plano. Com firewall em modo de
teste, o banco muda mas nenhuma regra de rede é aplicada.

## Janela para abrir o banco

Ao tocar em **Liberar 5 minutos para pagar**, o cliente recebe acesso temporário
à internet e a solicitação já aparece como `pending`. O mesmo IP/MAC só pode abrir
uma nova janela após o cooldown configurado, por padrão 30 minutos. Se o pagamento
for aprovado durante a janela, a sessão temporária é substituída pela sessão do
plano comprado.

## Criar voucher

No painel:

1. Escolha o plano.
2. Defina a quantidade máxima de usos.
3. Clique em **Gerar código**.
4. Entregue o código ao cliente.

Evite reutilizar vouchers de um uso. O histórico registra a quantidade consumida.

## Inspeção pelo terminal

```bash
cd ~/wifacil-turbo
tail -f data/server.log
ps -p "$(cat data/server.pid)"
```

Consulta rápida ao banco:

```bash
python - <<'PY'
import sqlite3
c = sqlite3.connect('data/wifacil.db')
for row in c.execute("select client_ip,plan_id,expires_at,status from sessions order by id desc limit 20"):
    print(row)
PY
```

## Encerramento seguro

```bash
cd ~/wifacil-turbo
./stop.sh
su -c './firewall.sh stop'
```

O último comando remove somente as cadeias criadas pelo projeto.
