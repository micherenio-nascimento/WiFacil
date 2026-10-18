# Termux e acesso pelo Ubuntu

## Fontes dos aplicativos

O F-Droid foi instalado a partir de `https://f-droid.org/F-Droid.apk` e o Termux
foi obtido do repositório F-Droid. Não misture Termux e plugins assinados por
fontes diferentes.

Versões registradas:

```text
F-Droid 2.0.1 (2000051)
Termux 0.118.3 (1002)
```

O Android inicialmente respondeu `INSTALL_FAILED_VERIFICATION_FAILURE`. Como o
APK veio da fonte oficial e foi validado, o verificador por ADB foi desativado
temporariamente, o pacote foi instalado e a configuração foi imediatamente
restaurada. Esse contorno não deve permanecer ativo.

## Pacotes do Termux

No Termux:

```bash
pkg update
pkg install openssh python
```

O aparelho usa arquitetura `armv7l`. A instalação do Python também fornece o
módulo padrão `sqlite3`.

## SSH pelo cabo USB

Inicie o servidor no Termux:

```bash
sshd
```

No Ubuntu:

```bash
adb forward tcp:8022 tcp:8022
```

Foi criada uma chave exclusiva:

```text
~/.ssh/termux_a01core
```

Somente a chave pública deve ser copiada para:

```text
/data/data/com.termux/files/home/.ssh/authorized_keys
```

Exemplo de `~/.ssh/config`:

```sshconfig
Host termux-a01
    HostName 127.0.0.1
    Port 8022
    User u0_a172
    IdentityFile ~/.ssh/termux_a01core
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
```

O UID `u0_a172` pode mudar se o aplicativo for removido e instalado novamente.
Consulte o valor atual com:

```bash
adb shell dumpsys package com.termux | grep -m1 userId=
```

Depois, conecte:

```bash
ssh termux-a01
```

Teste registrado:

```text
uid=10172(u0_a172) ... groups=3003(inet),9997(everybody),...
/data/data/com.termux/files/home
```

## Por que não usar somente `adb shell`?

`adb shell` abre o ambiente do usuário de depuração do Android, não o prefixo do
Termux. SSH entra no usuário do aplicativo e disponibiliza seus binários, `$HOME`,
pacotes e arquivos. O ADB é usado apenas como transporte USB.

## Após reiniciar o aparelho

1. Abra o Termux.
2. Execute `sshd`.
3. No Ubuntu, execute `adb forward tcp:8022 tcp:8022`.
4. Entre com `ssh termux-a01`.

Uma etapa futura pode instalar Termux:Boot, desde que venha da mesma fonte de
assinatura do Termux, para iniciar os serviços automaticamente.
