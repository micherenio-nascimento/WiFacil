# Segurança e privacidade

## Credenciais

- `.env` é ignorado pelo Git.
- A senha administrativa deve ser exclusiva e ter pelo menos 10 caracteres.
- O banco guarda somente PBKDF2-HMAC-SHA256 com 310 mil iterações e salt.
- `session.secret` é gerado aleatoriamente e deve permanecer privado.
- Chaves privadas SSH nunca devem entrar no repositório.

Uma senha que tenha sido enviada em chat, log ou captura deve ser considerada
exposta e substituída antes do uso público.

## Root

O backend roda como usuário do Termux. Somente ações de firewall invocam `su`.
Revise a solicitação do Magisk e conceda acesso apenas ao Termux legítimo. Root
amplia o impacto de qualquer vulnerabilidade no aplicativo ou no portal.

## Painel

O cookie administrativo é `HttpOnly`, `SameSite=Strict` e expira após oito horas.
Como o serviço usa HTTP local, não exponha a porta 8080 diretamente à internet.
No hotspot, considere limitar o painel à administração USB ou a um IP confiável
em uma versão futura.

## Dados pessoais

Colete o mínimo possível. A observação Pix é opcional e limitada a 80 caracteres.
Defina uma política de retenção para IPs, MACs, solicitações e sessões. Não peça
senha bancária nem armazene comprovantes desnecessariamente.

## Pix manual

O cliente copiará uma chave pública destinada a receber pagamentos. A aprovação
deve ocorrer somente após conferir o crédito efetivo no extrato. Não confie em:

- imagem de comprovante;
- texto copiado pelo cliente;
- promessa de agendamento;
- notificação fora do aplicativo bancário oficial.

## Rede e responsabilidade

O responsável pelo hotspot deve avaliar termos da operadora, legislação local,
registro de acesso aplicável e riscos de abuso da conexão. Considere limites de
velocidade, quantidade de clientes e bloqueio de portas abusivas antes do uso
comercial.
