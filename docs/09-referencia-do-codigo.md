# Referência do código

## `src/app.py`

Backend sem dependências externas, baseado na biblioteca padrão do Python.

### Inicialização

- Carrega `config.json`.
- Cria `data/` e um segredo aleatório de sessão.
- Inicializa tabelas SQLite.
- Lê `WIFACIL_ADMIN_PASSWORD` apenas na criação da senha.
- Inicia a thread de expiração.
- Escuta em `0.0.0.0:8080`.

### Rotas públicas

| Método | Rota | Função |
|---|---|---|
| GET | `/` | Portal, planos, estado do cliente |
| POST | `/request-pix` | Criar solicitação manual de Pix |
| POST | `/payment-window` | Criar solicitação e liberar internet temporária |
| POST | `/redeem` | Validar voucher e criar sessão |

Qualquer caminho HTTP desconhecido mostra o portal. Isso ajuda as sondagens de
detecção de portal cativo.

### Rotas administrativas

| Método | Rota | Função |
|---|---|---|
| GET | `/admin` | Formulário de login |
| POST | `/admin/login` | Validar senha e emitir cookie |
| GET | `/admin/dashboard` | Solicitações, vouchers e sessões |
| POST | `/admin/approve` | Aprovar Pix e ativar sessão |
| POST | `/admin/reject` | Rejeitar solicitação |
| POST | `/admin/voucher` | Gerar voucher |
| GET | `/logout` | Encerrar cookie administrativo |

### Funções relevantes

- `password_hash()` e `check_password()`: derivação PBKDF2.
- `client_mac()`: consulta vizinhança IP/MAC por `su`.
- `activate_session()`: substitui sessão anterior e libera o IP.
- `expire_sessions()`: revoga sessões vencidas.
- `firewall()`: única ponte do backend para operações privilegiadas.

## `src/firewall.sh`

Subcomandos:

```text
init IFACE GATEWAY [PORT]
allow IP
revoke IP
stop
status
```

As cadeias globais do Android nunca são esvaziadas. O script insere apenas saltos
para cadeias próprias e sabe removê-los.

## `src/start.sh` e `src/stop.sh`

`start.sh` carrega `.env`, evita instâncias duplicadas, inicia o Python em segundo
plano e grava PID/log. `stop.sh` encerra apenas o PID registrado.

## `src/config.json`

Configuração não secreta do portal. `price_cents` é inteiro; `minutes` determina
a expiração. `data_mb` é informativo na versão atual.
