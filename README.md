# WiFácil Turbo

Portal cativo de baixo custo executado em um **Samsung Galaxy A01 Core
SM-A013M com Android 10, root Magisk e Termux**.

O celular recebe internet 4G, oferece um hotspot Wi-Fi e mantém clientes sem
pagamento em um portal local. O acesso pode ser liberado por aprovação manual
de Pix ou por voucher, com sessões registradas no SQLite e expiração automática.

> **Estado atual no SM-A013M:** backend, portal, painel, Pix manual, vouchers,
> sessões e firewall estão implementados e testados. A interface validada é
> `swlan0`, com gateway observado `192.168.43.46`. O portal usa `REDIRECT` para a
> porta 8080 e bloqueia o contorno por IPv6.

## Visão geral

```text
4G / rede móvel
      │
      ▼
Galaxy A01 Core (Android + Magisk)
      │
      ├── Hotspot Wi-Fi
      │      └── clientes sem sessão → portal cativo
      │
      ├── Termux + Python
      │      ├── portal e painel HTTP
      │      ├── SQLite
      │      └── expiração de sessões
      │
      └── root + iptables
             ├── bloqueio de clientes pendentes
             └── liberação de IPs aprovados
```

## Funcionalidades

- Portal responsivo chamado **WiFácil Turbo**.
- Planos configuráveis em [`src/config.json`](src/config.json).
- Chave Pix com botão de cópia.
- Solicitação de aprovação manual após o pagamento.
- Janela de internet de 5 minutos para abrir o aplicativo bancário, protegida
  por cooldown de 30 minutos por IP/MAC.
- Painel administrativo autenticado.
- Vouchers com limite de usos.
- Sessões temporárias e expiração automática.
- Persistência SQLite em modo WAL.
- Senha armazenada com PBKDF2-HMAC-SHA256 e salt aleatório.
- Firewall em cadeias próprias, removíveis sem apagar regras do Android.
- Entrega do portal por `iptables REDIRECT`, compatível com a política de
  roteamento observada no Samsung.
- Acesso ao Termux pelo Ubuntu via SSH sobre USB.

## Documentação

1. [Histórico e ativação do root](docs/01-root-sm-a013m.md)
2. [Instalação e acesso ao Termux](docs/02-termux-e-ssh.md)
3. [Arquitetura e fluxo de negócio](docs/03-arquitetura.md)
4. [Instalação do WiFácil Turbo](docs/04-instalacao.md)
5. [Operação diária](docs/05-operacao.md)
6. [Firewall e portal cativo](docs/06-firewall.md)
7. [Segurança](docs/07-seguranca.md)
8. [Solução de problemas](docs/08-troubleshooting.md)
9. [Referência do código](docs/09-referencia-do-codigo.md)

Consulte também o [histórico de alterações](CHANGELOG.md).

## Início rápido do backend

No Termux:

```bash
pkg update
pkg install python openssh
cp -r /caminho/para/src ~/wifacil-turbo
cd ~/wifacil-turbo
cp .env.example .env
nano .env
chmod 700 start.sh stop.sh firewall.sh
./start.sh
```

Portal: `http://127.0.0.1:8080/`  
Painel: `http://127.0.0.1:8080/admin`

Para testar pelo Ubuntu conectado por USB:

```bash
adb forward tcp:8080 tcp:8080
xdg-open http://127.0.0.1:8080/
```

## Avisos

- Desbloquear o bootloader apaga os dados e reduz a segurança do aparelho.
- Flash de firmware incorreto pode impedir a inicialização.
- O procedimento de root documentado é específico para o modelo e revisão
  indicados; não reutilize os arquivos binários em outro aparelho.
- Não habilite o firewall antes de confirmar a interface e o gateway do hotspot.
- Confira o crédito no aplicativo bancário; comprovantes e capturas de tela não
  constituem confirmação de pagamento.
- Verifique regras locais sobre revenda/compartilhamento de dados móveis e os
  termos da operadora.

## Licença

Consulte [`LICENSE`](LICENSE). O software é fornecido sem garantia.
