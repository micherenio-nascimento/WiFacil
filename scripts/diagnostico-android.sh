#!/usr/bin/env bash
set -euo pipefail

echo "== Dispositivo ADB =="
adb devices -l

echo "== Modelo e build =="
adb shell getprop ro.product.model
adb shell getprop ro.build.display.id

echo "== Estado de boot =="
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.device_state

echo "== Root =="
adb shell su -c id

echo "== Interfaces (somente leitura) =="
adb shell su -c 'ip -brief address'

echo "== Rotas (somente leitura) =="
adb shell su -c 'ip route show table all'

echo "== Cadeias WiFácil =="
adb shell su -c 'iptables -t nat -S WIFACIL_PORTAL 2>/dev/null || true'
adb shell su -c 'iptables -S WIFACIL_ACCESS 2>/dev/null || true'
