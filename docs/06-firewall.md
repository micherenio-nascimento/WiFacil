# Firewall e portal cativo

## Princípio

O script cria duas cadeias próprias:

```text
nat/WIFACIL_PORTAL
filter/WIFACIL_ACCESS
```

Clientes não autorizados:

- HTTP na porta 80 é entregue localmente ao portal na porta 8080 com o alvo
  `REDIRECT` do iptables;
- tráfego encaminhado à internet é rejeitado.
- encaminhamento IPv6 é rejeitado para impedir contorno do portal; a versão
  atual fornece o acesso autorizado pela rota IPv4.

Clientes autorizados recebem uma regra `RETURN` no redirecionamento e uma regra
`ACCEPT` no encaminhamento.

## Por que validar antes de ligar o firewall

Em uma instalação nova, mantenha o firewall desligado até medir a rede. O nome
da interface do hotspot varia por fabricante e versão (`wlan0`, `ap0`,
`swlan0` ou outro). Escolher a interface errada pode bloquear a administração ou
interferir nas regras de tethering do Android.

No Galaxy A01 Core testado, a medição com o hotspot ativo em 17/10/2026 foi
concluída e a configuração operacional passou a usar:

```text
interface: swlan0
gateway: 192.168.43.46
primeiro cliente observado: 192.168.43.47
```

O primeiro cliente é apenas um exemplo e não deve ser fixado na configuração.

Com o hotspot ligado, descubra a interface:

```bash
adb shell su -c 'ip -brief address'
adb shell su -c 'ip route show table all'
adb shell su -c 'iptables -t nat -S'
adb shell su -c 'iptables -S FORWARD'
```

Procure a interface com endereço de gateway da rede oferecida aos clientes. Em
muitos aparelhos Samsung/Android 10 o gateway pode ser `192.168.43.1`, mas ele
deve ser medido, não presumido.

## Ativação manual controlada

Depois de confirmar interface e gateway:

```bash
cd ~/wifacil-turbo
su -c './firewall.sh init INTERFACE GATEWAY 8080'
su -c './firewall.sh status'
```

Teste com um segundo aparelho antes de definir `firewall_enabled` como `true`.

Liberação e revogação isoladas:

```bash
su -c './firewall.sh allow 192.168.43.20'
su -c './firewall.sh revoke 192.168.43.20'
```

Remoção completa:

```bash
su -c './firewall.sh stop'
```

## Salvaguardas

- O script não executa `iptables -F` nas cadeias globais.
- As regras de salto são removidas antes de excluir as cadeias próprias.
- O estado da interface fica em `data/firewall.state`.
- Uma regra `INPUT` limitada à interface do hotspot e à porta do portal permite
  que os clientes alcancem o backend sem expor outras portas.
- Mantenha o cabo USB conectado no primeiro teste para recuperação via ADB.

## Portal cativo e HTTPS

Não faça interceptação TLS. Ela apresentaria alertas de certificado e criaria
riscos de segurança. O portal depende das sondagens HTTP dos sistemas operacionais
e do acesso manual ao endereço do gateway.
