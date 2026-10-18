# Solução de problemas

## ADB não inicia no ambiente isolado

Sintoma:

```text
could not install *smartsocket* listener: Operation not permitted
```

Execute o ADB no Ubuntu real, fora de um sandbox, e confirme:

```bash
adb kill-server
adb start-server
adb devices -l
```

## Odin/USB retorna `-7` ou `-71`

- troque cabo e porta;
- evite hubs;
- mantenha o aparelho imóvel;
- acompanhe `sudo dmesg -wT`;
- não grave enquanto houver desconexões;
- confirme a listagem repetidamente antes do flash.

## Erro de digest no Download Mode

Mensagens como `Hash of data does not match digest in descriptor` indicam que
partições verificadas por AVB não formam um conjunto coerente. Não continue
misturando `boot`, `vbmeta` e AP de builds diferentes. Restaure o conjunto stock
e repita o patch do AP correspondente.

## `failed the resizing-data`

Após mudança de firmware/partições, o recovery pode exigir **Factory data reset**.
Isso apaga todos os dados. Só execute quando houver backup e firmware recuperável.

## `INSTALL_FAILED_VERIFICATION_FAILURE`

Baixe APKs apenas da fonte oficial e confira sua origem. Se for necessário
desativar o verificador por ADB em um aparelho de laboratório com root, restaure
a configuração imediatamente após instalar. Não deixe a proteção desligada.

## `run-as: package not debuggable`

A versão estável do Termux não aceita `run-as`. Use SSH dentro do próprio Termux.
Ao automatizar via root, preserve o UID e os grupos do processo, especialmente o
grupo `inet` (normalmente GID 3003), ou o DNS/rede poderá falhar.

## SSH recusa conexão

```bash
# no celular/Termux
sshd

# no Ubuntu
adb forward --remove tcp:8022 2>/dev/null || true
adb forward tcp:8022 tcp:8022
ssh -v termux-a01
```

Verifique se o usuário configurado ainda coincide com o UID atual do Termux.

## Portal não responde

```bash
cd ~/wifacil-turbo
cat data/server.pid
tail -100 data/server.log
./stop.sh
./start.sh
```

No Ubuntu:

```bash
adb forward tcp:8080 tcp:8080
curl -v http://127.0.0.1:8080/
```

## Cliente continua sem internet após aprovação

1. Confirme que `firewall_enabled` está `true` somente depois da inicialização.
2. Compare o IP da sessão com o lease atual do cliente.
3. Execute `su -c './firewall.sh status'`.
4. Confira se a regra `ACCEPT` precede a regra final `REJECT`.
5. Verifique se o Android recriou as regras ao alternar o hotspot.

## HTTP é contado no NAT, mas o portal não abre

Algumas políticas Samsung/Android não entregam ao Termux pacotes enviados por
`DNAT` para o próprio endereço do hotspot. Use `REDIRECT --to-ports 8080` na
cadeia do portal e permita TCP/8080 em `INPUT` somente na interface do hotspot.
O script atual já implementa esse comportamento.

## Recuperação imediata do firewall

Com ADB USB:

```bash
adb shell su -c '/data/data/com.termux/files/home/wifacil-turbo/firewall.sh stop'
```

Esse comando remove apenas as cadeias do WiFácil.
