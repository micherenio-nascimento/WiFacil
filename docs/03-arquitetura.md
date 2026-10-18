# Arquitetura

## Componentes

| Componente | Responsabilidade |
|---|---|
| Android/Hotspot | Compartilhar a conexão móvel e fornecer DHCP aos clientes |
| Magisk `su` | Autorizar mudanças controladas no firewall |
| `iptables` | Redirecionar HTTP e bloquear/liberar encaminhamento |
| Python | Servir portal, painel e regras de negócio |
| SQLite | Persistir solicitações, vouchers, sessões e configuração segura |
| Termux | Ambiente de execução do backend |
| ADB/SSH | Administração local pelo Ubuntu através do USB |

## Fluxo Pix manual

```text
cliente conecta
  → portal mostra plano e chave Pix
  → cliente solicita uma janela de pagamento de 5 minutos
  → firewall libera temporariamente a internet para abrir o banco
  → solicitação pending já aparece no painel
  → cliente faz o Pix
  → solicitação fica pending
  → administrador confere o extrato bancário
  → administrador aprova
  → sessão active é criada
  → firewall libera o IP
  → prazo termina
  → sessão vira expired e o IP é removido
```

O sistema não considera capturas de tela como prova de pagamento. A conferência
é feita no aplicativo ou extrato da instituição financeira.

### Por que não liberar somente aplicativos bancários?

O `iptables` opera por endereços e portas, não pelo nome do aplicativo no aparelho
cliente. Bancos usam domínios, CDNs e IPs variáveis. Uma lista fixa quebraria o
pagamento ou liberaria serviços além do esperado. A janela temporária é limitada
por IP/MAC e possui cooldown de 30 minutos para reduzir abuso.

## Fluxo de voucher

```text
administrador gera código
  → cliente informa código
  → backend valida active, uses e max_uses
  → incrementa uses
  → cria sessão temporária
  → libera o cliente
```

## Modelo de dados

### `settings`

Armazena valores internos, incluindo somente o hash da senha administrativa.

### `pix_requests`

- IP e MAC conhecidos;
- plano e preço no momento da solicitação;
- observação opcional;
- estado `pending`, `approved`, `rejected` ou `cancelled`;
- datas de criação e decisão.

### `vouchers`

- código aleatório sem caracteres ambíguos;
- plano e duração;
- usos atuais e máximo permitido;
- estado ativo.

### `sessions`

- IP/MAC do cliente;
- origem `pix` ou `voucher`;
- plano;
- início, expiração e estado.

## Concorrência

O servidor usa `ThreadingHTTPServer`. O SQLite abre uma conexão por operação, usa
WAL e timeout de bloqueio. Uma thread verifica sessões vencidas a cada 20 segundos.

## Limitações atuais

- A identificação e as regras efetivas usam principalmente o IP. O lease DHCP
  deve ser estável durante a sessão.
- O HTTPS não pode ser redirecionado de forma transparente sem causar erro de
  certificado; sistemas operacionais normalmente detectam o portal por HTTP.
- A franquia em MB aparece no plano, mas a contabilização por cliente ainda não
  foi implementada. A versão atual expira por tempo.
- Reinicializações do subsistema de tethering podem reconstruir regras Android;
  o serviço deverá reconciliar as cadeias quando isso ocorrer.
- O Galaxy A01 Core possui recursos limitados; comece com poucos clientes.
