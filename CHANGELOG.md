# Histórico de alterações

## 2026-10-17

### Portal e pagamentos

- Criado o portal **WiFácil Turbo** com três planos.
- Adicionada chave Pix copiável e aprovação manual no painel.
- Adicionados vouchers com limite de usos.
- Adicionadas sessões SQLite com expiração automática.
- Adicionada janela de internet de 5 minutos para o cliente abrir o aplicativo
  bancário e realizar o Pix.
- Adicionado cooldown padrão de 30 minutos por IP/MAC para reduzir abuso da
  janela temporária.

### Rede e firewall

- Interface do hotspot identificada como `swlan0`.
- Gateway observado como `192.168.43.46`.
- Criadas cadeias isoladas `WIFACIL_PORTAL`, `WIFACIL_ACCESS` e
  `WIFACIL6_ACCESS`.
- Bloqueado encaminhamento IPv6 para impedir contorno do controle IPv4.
- Substituído `DNAT gateway:8080` por `REDIRECT --to-ports 8080`. O DNAT era
  contado, mas a política de roteamento Samsung não entregava a conexão ao
  processo Termux.
- Adicionada permissão `INPUT` limitada a TCP/8080 na interface do hotspot.
- Confirmada a entrega do cliente `192.168.43.47` ao backend com respostas HTTP
  200 para `/` e `/generate_204`.

### Segurança e documentação

- Removida senha provisória do código-fonte.
- Senha inicial movida para `.env` e armazenada no SQLite somente como PBKDF2.
- Adicionados guias de root, Termux/SSH, arquitetura, instalação, operação,
  firewall, segurança, referência do código e troubleshooting.
