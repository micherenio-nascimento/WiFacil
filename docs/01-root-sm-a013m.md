# Root do Samsung Galaxy A01 Core SM-A013M

Este documento registra o procedimento realmente utilizado no aparelho de teste.
Ele não é um guia genérico para outros modelos.

## Ambiente validado

- Modelo: Samsung Galaxy A01 Core `SM-A013M`
- Android: 10
- Build: `QP1A.190711.020.A013MUBS3AWC1`
- Bootloader: `OEM LOCK: OFF (U)`
- Estado AVB depois do desbloqueio: `orange` / `unlocked`
- Host: Ubuntu Linux
- Magisk: 30.7
- Ferramenta final de flash: `samloader-rs 2.2.0`

Identificadores exclusivos do aparelho, números de série e DID foram omitidos.

## Riscos e pré-requisitos

1. Faça backup. O desbloqueio e as recuperações de erro apagam os dados.
2. Use firmware correspondente ao modelo e ao índice de bootloader.
3. Carregue a bateria e use um cabo de dados confiável.
4. Não desconecte durante a transmissão.
5. Mantenha uma cópia do firmware oficial completo para recuperação.

## Diagnóstico USB inicial

Com o aparelho em Download Mode:

```bash
lsusb | grep -i samsung
sudo ~/odin4/build/odin4 -l
sudo dmesg -wT
```

O dispositivo Samsung apareceu como `04e8:685d`. O cabo original produziu erros
como `USB bulk read failed (error: -7)` e `device descriptor ... error -71`.
O cabo e a porta foram trocados antes de qualquer nova gravação.

> Um `--check-only` que termina em `USB handshake failed` não autoriza flash.

## Desbloqueio do bootloader

Ativar apenas **Desbloqueio de OEM** nas opções do desenvolvedor não basta. O
estado foi confirmado tanto no Download Mode quanto por propriedades do Android.

Depois do desbloqueio e da restauração de fábrica:

```bash
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.device_state
```

Resultado esperado neste aparelho:

```text
0
orange
unlocked
```

No Download Mode, a confirmação visual foi:

```text
OEM LOCK: OFF (U)
```

## Firmware usado

Diretório de trabalho:

```text
~/firmware-a01core
```

Pacotes oficiais registrados:

```text
BL_A013MUBS3AWC1_CL20440625_QB63021732_REV00_user_low_ship_MULTI_CERT.tar.md5
CP_A013MUBS3AWB1_CP23734425_CL20440625_QB62628022_REV00_user_low_ship_MULTI_CERT.tar.md5
CSC_OMC_OWO_A013MOWO3AVE1_CL24313464_QB52330246_REV00_user_low_ship_MULTI_CERT.tar.md5
```

AP corrigido pelo Magisk:

```text
patched/magisk_patched-30700_IQafj.tar
```

O AP contém, entre outras imagens, `boot`, `recovery`, `dtbo`, `super`, `tee` e
`vbmeta`. Tentar combinar apenas `boot` corrigido com `vbmeta` stock produziu
falha de digest AVB. Também houve erro de cabeçalho com uma imagem `vbmeta`
incompatível. Por isso a solução foi gravar o AP corrigido como conjunto.

## CSC sem PIT

O PIT incluído no CSC não era idêntico ao PIT lido do aparelho. Para não
reparticionar, foi criado um CSC sem o arquivo PIT:

```text
samloader-packages/CSC_OMC_OWO_A013MOWO3AVE1_no_pit.tar
```

Conteúdo registrado:

```text
cache.img.lz4
omr.img.lz4
optics.img.lz4
prism.img.lz4
meta-data/fota.zip
```

Não use esse artefato em outro modelo ou firmware sem repetir a análise do PIT.

## Flash que concluiu com sucesso

Foi usado o projeto open source
[`topjohnwu/samloader-rs`](https://github.com/topjohnwu/samloader-rs), versão
2.2.0. O procedimento enviou:

- BL oficial;
- AP completo corrigido pelo Magisk;
- CP oficial;
- CSC oficial sem PIT.

O log terminou com protocolo concluído, resposta `CloseConnection` igual a zero
e status de saída zero. O log local foi preservado originalmente como:

```text
~/firmware-a01core/samloader-magisk.log
```

Os argumentos exatos dependem da interface da versão instalada. Antes de repetir:

```bash
~/samloader-2.2.0/samloader --help
```

Não use opções equivalentes a `--efs-clear`, `--allow-unknown` ou atualização
forçada do bootloader sem compreender suas consequências.

## Primeiro boot

O recovery exibiu:

```text
Resizing data...
failed the resizing-data
```

Foi executado **Factory data reset** e depois **Reboot system now**. Essa etapa
apagou os dados, mas permitiu que o Android recriasse `/data`.

## Verificação final do root

Após iniciar o Android e instalar/abrir o Magisk:

```bash
adb shell getprop sys.boot_completed
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.verifiedbootstate
adb shell su -c id
```

Resultado decisivo:

```text
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

O processo `magiskd`, `/sbin/su` e o pacote `com.topjohnwu.magisk` também foram
encontrados. Não foi necessário usar novamente a opção **Instalação direta**.

## Recuperação registrada

Durante os testes houve telas de erro de atualização, falhas de digest e retorno
ao recovery. O aparelho foi recuperado gravando o firmware oficial completo com
Heimdall 2.1.0 e realizando a restauração de fábrica. Mantenha sempre um caminho
de recuperação stock antes de alterar AVB, `boot` ou `vbmeta`.
