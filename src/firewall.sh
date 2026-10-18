#!/data/data/com.termux/files/usr/bin/bash
set -eu

IPTABLES=/system/bin/iptables
IP6TABLES=/system/bin/ip6tables
NAT_CHAIN=WIFACIL_PORTAL
FILTER_CHAIN=WIFACIL_ACCESS
FILTER6_CHAIN=WIFACIL6_ACCESS
STATE_DIR=/data/data/com.termux/files/home/wifacil-turbo/data
STATE_FILE="$STATE_DIR/firewall.state"

ensure_chain() {
  table="$1" chain="$2"
  "$IPTABLES" -t "$table" -N "$chain" 2>/dev/null || true
  "$IPTABLES" -t "$table" -F "$chain"
}

case "${1:-}" in
  init)
    iface="${2:?interface ausente}"
    gateway="${3:?gateway ausente}"
    port="${4:-8080}"
    mkdir -p "$STATE_DIR"
    ensure_chain nat "$NAT_CHAIN"
    ensure_chain filter "$FILTER_CHAIN"
    "$IP6TABLES" -N "$FILTER6_CHAIN" 2>/dev/null || true
    "$IP6TABLES" -F "$FILTER6_CHAIN"
    "$IPTABLES" -t nat -C PREROUTING -i "$iface" -p tcp --dport 80 -j "$NAT_CHAIN" 2>/dev/null || \
      "$IPTABLES" -t nat -I PREROUTING 1 -i "$iface" -p tcp --dport 80 -j "$NAT_CHAIN"
    "$IPTABLES" -C FORWARD -i "$iface" -j "$FILTER_CHAIN" 2>/dev/null || \
      "$IPTABLES" -I FORWARD 1 -i "$iface" -j "$FILTER_CHAIN"
    "$IPTABLES" -C INPUT -i "$iface" -p tcp --dport "$port" -j ACCEPT 2>/dev/null || \
      "$IPTABLES" -I INPUT 1 -i "$iface" -p tcp --dport "$port" -j ACCEPT
    "$IP6TABLES" -C FORWARD -i "$iface" -j "$FILTER6_CHAIN" 2>/dev/null || \
      "$IP6TABLES" -I FORWARD 1 -i "$iface" -j "$FILTER6_CHAIN"
    # REDIRECT funciona mesmo quando a política de roteamento do fabricante não
    # trata o endereço do hotspot como destino local para apps do Termux.
    "$IPTABLES" -t nat -A "$NAT_CHAIN" -p tcp --dport 80 -j REDIRECT --to-ports "$port"
    "$IPTABLES" -A "$FILTER_CHAIN" -j REJECT
    # Evita que clientes contornem o portal pela conectividade IPv6 do tethering.
    # A versão atual fornece acesso pago por IPv4.
    "$IP6TABLES" -A "$FILTER6_CHAIN" -j REJECT
    printf '%s %s %s\n' "$iface" "$gateway" "$port" > "$STATE_FILE"
    ;;
  allow)
    ip="${2:?IP ausente}"
    "$IPTABLES" -t nat -D "$NAT_CHAIN" -s "$ip" -j RETURN 2>/dev/null || true
    "$IPTABLES" -D "$FILTER_CHAIN" -s "$ip" -j ACCEPT 2>/dev/null || true
    "$IPTABLES" -t nat -I "$NAT_CHAIN" 1 -s "$ip" -j RETURN
    "$IPTABLES" -I "$FILTER_CHAIN" 1 -s "$ip" -j ACCEPT
    ;;
  revoke)
    ip="${2:?IP ausente}"
    while "$IPTABLES" -t nat -D "$NAT_CHAIN" -s "$ip" -j RETURN 2>/dev/null; do :; done
    while "$IPTABLES" -D "$FILTER_CHAIN" -s "$ip" -j ACCEPT 2>/dev/null; do :; done
    ;;
  stop)
    if [ -f "$STATE_FILE" ]; then
      read -r iface gateway port < "$STATE_FILE"
      "$IPTABLES" -t nat -D PREROUTING -i "$iface" -p tcp --dport 80 -j "$NAT_CHAIN" 2>/dev/null || true
      "$IPTABLES" -D FORWARD -i "$iface" -j "$FILTER_CHAIN" 2>/dev/null || true
      "$IPTABLES" -D INPUT -i "$iface" -p tcp --dport "$port" -j ACCEPT 2>/dev/null || true
      "$IP6TABLES" -D FORWARD -i "$iface" -j "$FILTER6_CHAIN" 2>/dev/null || true
    fi
    "$IPTABLES" -t nat -F "$NAT_CHAIN" 2>/dev/null || true
    "$IPTABLES" -t nat -X "$NAT_CHAIN" 2>/dev/null || true
    "$IPTABLES" -F "$FILTER_CHAIN" 2>/dev/null || true
    "$IPTABLES" -X "$FILTER_CHAIN" 2>/dev/null || true
    "$IP6TABLES" -F "$FILTER6_CHAIN" 2>/dev/null || true
    "$IP6TABLES" -X "$FILTER6_CHAIN" 2>/dev/null || true
    rm -f "$STATE_FILE"
    ;;
  status)
    "$IPTABLES" -t nat -S "$NAT_CHAIN" 2>/dev/null || true
    "$IPTABLES" -S "$FILTER_CHAIN" 2>/dev/null || true
    "$IP6TABLES" -S "$FILTER6_CHAIN" 2>/dev/null || true
    ;;
  *)
    echo "uso: $0 {init IFACE GATEWAY [PORT]|allow IP|revoke IP|stop|status}" >&2
    exit 2
    ;;
esac
