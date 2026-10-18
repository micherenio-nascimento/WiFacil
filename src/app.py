#!/data/data/com.termux/files/usr/bin/python
import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import subprocess
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB_PATH = DATA / "wifacil.db"
CONFIG_PATH = ROOT / "config.json"
SECRET_PATH = DATA / "session.secret"
FIREWALL = ROOT / "firewall.sh"
DATA.mkdir(exist_ok=True)


def now_ts():
    return int(time.time())


def dt(ts):
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


CFG = load_config()
if not SECRET_PATH.exists():
    SECRET_PATH.write_text(secrets.token_hex(32), encoding="ascii")
    os.chmod(SECRET_PATH, 0o600)
SECRET = SECRET_PATH.read_text(encoding="ascii").strip().encode()


def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def password_hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return base64.b64encode(salt).decode() + ":" + base64.b64encode(digest).decode()


def check_password(password, stored):
    try:
        salt64, expected64 = stored.split(":", 1)
        candidate = password_hash(password, base64.b64decode(salt64)).split(":", 1)[1]
        return hmac.compare_digest(candidate, expected64)
    except Exception:
        return False


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS pix_requests(
          id INTEGER PRIMARY KEY AUTOINCREMENT, client_ip TEXT NOT NULL, client_mac TEXT,
          plan_id TEXT NOT NULL, price_cents INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
          note TEXT, created_at INTEGER NOT NULL, decided_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS vouchers(
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, plan_id TEXT NOT NULL,
          minutes INTEGER NOT NULL, max_uses INTEGER NOT NULL DEFAULT 1, uses INTEGER NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions(
          id INTEGER PRIMARY KEY AUTOINCREMENT, client_ip TEXT NOT NULL, client_mac TEXT,
          source TEXT NOT NULL, source_id INTEGER, plan_id TEXT NOT NULL,
          started_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active'
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(status, expires_at);
        """)
        # A senha inicial vem apenas do ambiente e nunca deve ser versionada.
        exists = con.execute("SELECT 1 FROM settings WHERE key='admin_password'").fetchone()
        if not exists:
            initial_password = os.environ.get("WIFACIL_ADMIN_PASSWORD", "")
            if len(initial_password) < 10:
                raise RuntimeError(
                    "Defina WIFACIL_ADMIN_PASSWORD com pelo menos 10 caracteres no arquivo .env"
                )
            con.execute(
                "INSERT INTO settings(key,value) VALUES('admin_password',?)",
                (password_hash(initial_password),),
            )


def client_mac(ip):
    try:
        out = subprocess.check_output(["su", "-c", f"ip neigh show {ip}"], text=True, timeout=2)
        parts = out.split()
        return parts[parts.index("lladdr") + 1] if "lladdr" in parts else ""
    except Exception:
        return ""


def firewall(action, ip=None):
    if not CFG.get("firewall_enabled"):
        return True, "firewall em modo de teste"
    cmd = ["su", "-c", f"{FIREWALL} {action}" + (f" {ip}" if ip else "")]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=10)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def activate_session(con, ip, mac, source, source_id, plan_id, minutes):
    start = now_ts()
    expires = start + int(minutes) * 60
    con.execute("UPDATE sessions SET status='replaced' WHERE client_ip=? AND status='active'", (ip,))
    cur = con.execute("""INSERT INTO sessions
        (client_ip,client_mac,source,source_id,plan_id,started_at,expires_at,status)
        VALUES(?,?,?,?,?,?,?,'active')""", (ip, mac, source, source_id, plan_id, start, expires))
    ok, message = firewall("allow", ip)
    if not ok:
        raise RuntimeError("Falha no firewall: " + message)
    return cur.lastrowid, expires


def expire_sessions():
    while True:
        try:
            with db() as con:
                rows = con.execute("SELECT id,client_ip FROM sessions WHERE status='active' AND expires_at<=?", (now_ts(),)).fetchall()
                for row in rows:
                    firewall("revoke", row["client_ip"])
                    con.execute("UPDATE sessions SET status='expired' WHERE id=?", (row["id"],))
        except Exception as exc:
            print("expiration error:", exc, flush=True)
        time.sleep(20)


STYLE = """
:root{--blue:#075985;--cyan:#06b6d4;--green:#16a34a;--bg:#f0f9ff;--ink:#0f172a}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:linear-gradient(135deg,#e0f2fe,#ecfdf5);color:var(--ink)}
.wrap{max-width:850px;margin:auto;padding:22px}.hero{text-align:center;padding:20px}.logo{font-size:2.2rem;font-weight:900;color:var(--blue)}
.tag{color:#475569}.card{background:#fff;border-radius:18px;padding:22px;margin:14px 0;box-shadow:0 10px 28px #07598518}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.plan{border:2px solid #bae6fd;border-radius:14px;padding:14px}
.price{font-size:1.7rem;font-weight:850;color:var(--green)}button,.btn{background:var(--blue);color:white;border:0;border-radius:10px;padding:12px 16px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}
button.good{background:var(--green)}button.bad{background:#dc2626}input,select{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;margin:5px 0 12px}
table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{text-align:left;padding:9px;border-bottom:1px solid #e2e8f0}.msg{padding:12px;border-radius:10px;background:#dcfce7}.warn{background:#fef3c7}
.pix{font-family:monospace;word-break:break-all;background:#f1f5f9;padding:12px;border-radius:9px}.nav{display:flex;gap:8px;flex-wrap:wrap}.muted{color:#64748b;font-size:.9rem}
"""


def page(title, body):
    return f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main class='wrap'>{body}</main></body></html>"""


def money(cents):
    return f"R$ {cents/100:.2f}".replace(".", ",")


def plan_by_id(plan_id):
    return next((p for p in CFG["plans"] if p["id"] == plan_id), None)


def signed_cookie():
    expiry = now_ts() + 8 * 3600
    value = f"admin:{expiry}"
    sig = hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{value}:{sig}".encode()).decode()


def cookie_valid(raw):
    try:
        decoded = base64.urlsafe_b64decode(raw.encode()).decode()
        role, expiry, sig = decoded.split(":")
        expected = hmac.new(SECRET, f"{role}:{expiry}".encode(), hashlib.sha256).hexdigest()
        return role == "admin" and int(expiry) > now_ts() and hmac.compare_digest(sig, expected)
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "WiFacil/1.0"

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} {fmt % args}", flush=True)

    def send_html(self, content, status=200, headers=None):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303); self.send_header("Location", location); self.end_headers()

    def form(self):
        length = min(int(self.headers.get("Content-Length", "0")), 16_384)
        return {k: v[-1] for k, v in urllib.parse.parse_qs(self.rfile.read(length).decode()).items()}

    def is_admin(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        return "wfadmin" in cookie and cookie_valid(cookie["wfadmin"].value)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/admin": return self.admin_login()
        if path == "/admin/dashboard": return self.dashboard()
        if path == "/logout": return self.logout()
        return self.portal()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        routes = {"/request-pix": self.request_pix, "/redeem": self.redeem,
                  "/payment-window": self.payment_window,
                  "/admin/login": self.login, "/admin/approve": self.approve,
                  "/admin/reject": self.reject, "/admin/voucher": self.create_voucher}
        handler = routes.get(path)
        if not handler: return self.send_error(404)
        return handler()

    def portal(self, message=""):
        ip = self.client_address[0]
        with db() as con:
            active = con.execute("SELECT * FROM sessions WHERE client_ip=? AND status='active' AND expires_at>? ORDER BY id DESC LIMIT 1", (ip, now_ts())).fetchone()
            pending = con.execute("SELECT * FROM pix_requests WHERE client_ip=? AND status='pending' ORDER BY id DESC LIMIT 1", (ip,)).fetchone()
        plans = "".join(f"<div class='plan'><b>{html.escape(p['name'])}</b><div class='price'>{money(p['price_cents'])}</div><div>{p['minutes']} minutos · {p['data_mb']} MB</div></div>" for p in CFG["plans"])
        options = "".join(f"<option value='{p['id']}'>{html.escape(p['name'])} — {money(p['price_cents'])}</option>" for p in CFG["plans"])
        status = ""
        if active: status = f"<div class='msg'>Internet liberada até <b>{dt(active['expires_at'])}</b>.</div>"
        elif pending: status = "<div class='msg warn'>Pagamento aguardando conferência do administrador.</div>"
        if message: status += f"<div class='msg'>{html.escape(message)}</div>"
        body = f"""<section class='hero'><div class='logo'>⚡ {html.escape(CFG['portal_name'])}</div><div class='tag'>{html.escape(CFG['slogan'])}</div></section>
        {status}<section class='plans'>{plans}</section>
        <section class='card'><h2>Pagar com Pix</h2><p>Envie o valor do plano para:</p><div class='pix' id='pix'>{html.escape(CFG['pix_key'])}</div>
        <p><button onclick="navigator.clipboard.writeText(document.getElementById('pix').innerText)">Copiar chave Pix</button></p>
        <form method='post' action='/payment-window'><label>Plano</label><select name='plan_id'>{options}</select><label>Observação opcional</label><input name='note' maxlength='80' placeholder='Ex.: nome usado no pagamento'><button class='good'>Liberar 5 minutos para pagar</button></form>
        <p class='muted'>A internet será liberada temporariamente para você abrir o aplicativo do banco. A solicitação ficará aguardando a conferência do pagamento.</p>
        <form method='post' action='/request-pix'><label>Se pagou usando outra conexão</label><select name='plan_id'>{options}</select><button>Informar pagamento</button></form></section>
        <section class='card'><h2>Tenho um código</h2><form method='post' action='/redeem'><input name='code' required maxlength='32' autocomplete='off' placeholder='Digite o código de acesso'><button>Conectar</button></form></section>
        <p class='muted'>Dispositivo: {html.escape(ip)} · <a href='/admin'>Administração</a></p>"""
        self.send_html(page(CFG["portal_name"], body))

    def request_pix(self):
        f = self.form(); plan = plan_by_id(f.get("plan_id", ""))
        if not plan: return self.portal("Plano inválido.")
        ip = self.client_address[0]; mac = client_mac(ip)
        with db() as con:
            con.execute("UPDATE pix_requests SET status='cancelled',decided_at=? WHERE client_ip=? AND status='pending'", (now_ts(), ip))
            con.execute("INSERT INTO pix_requests(client_ip,client_mac,plan_id,price_cents,note,created_at) VALUES(?,?,?,?,?,?)", (ip,mac,plan['id'],plan['price_cents'],f.get('note','')[:80],now_ts()))
        self.redirect("/")

    def payment_window(self):
        f = self.form(); plan = plan_by_id(f.get("plan_id", ""))
        if not plan: return self.portal("Plano inválido.")
        ip = self.client_address[0]; mac = client_mac(ip)
        minutes = int(CFG.get("payment_window_minutes", 5))
        cooldown = int(CFG.get("payment_window_cooldown_minutes", 30)) * 60
        with db() as con:
            if mac:
                recent = con.execute("""SELECT started_at FROM sessions
                    WHERE source='payment_window' AND (client_mac=? OR client_ip=?)
                    ORDER BY id DESC LIMIT 1""", (mac, ip)).fetchone()
            else:
                recent = con.execute("""SELECT started_at FROM sessions
                    WHERE source='payment_window' AND client_ip=?
                    ORDER BY id DESC LIMIT 1""", (ip,)).fetchone()
            if recent and recent["started_at"] > now_ts() - cooldown:
                remaining = max(1, (recent["started_at"] + cooldown - now_ts() + 59) // 60)
                return self.portal(f"A janela de pagamento já foi utilizada. Tente novamente em {remaining} minuto(s) ou peça ajuda ao administrador.")
            con.execute("UPDATE pix_requests SET status='cancelled',decided_at=? WHERE client_ip=? AND status='pending'", (now_ts(), ip))
            cur = con.execute("""INSERT INTO pix_requests
                (client_ip,client_mac,plan_id,price_cents,note,created_at)
                VALUES(?,?,?,?,?,?)""", (ip,mac,plan['id'],plan['price_cents'],f.get('note','')[:80],now_ts()))
            activate_session(con, ip, mac, "payment_window", cur.lastrowid, plan["id"], minutes)
        self.portal(f"Internet liberada por {minutes} minutos. Abra o aplicativo do banco e faça o Pix.")

    def redeem(self):
        code = self.form().get("code", "").strip().upper()
        ip = self.client_address[0]; mac = client_mac(ip)
        try:
            with db() as con:
                v = con.execute("SELECT * FROM vouchers WHERE code=? AND active=1 AND uses<max_uses", (code,)).fetchone()
                if not v: return self.portal("Código inválido ou já utilizado.")
                activate_session(con, ip, mac, "voucher", v["id"], v["plan_id"], v["minutes"])
                con.execute("UPDATE vouchers SET uses=uses+1 WHERE id=?", (v["id"],))
            self.portal("Código aceito. Acesso liberado!")
        except Exception as exc: self.portal(str(exc))

    def admin_login(self, error=""):
        msg = f"<div class='msg warn'>{html.escape(error)}</div>" if error else ""
        self.send_html(page("Admin", f"<div class='card'><h1>WiFácil Turbo — Administração</h1>{msg}<form method='post' action='/admin/login'><label>Senha</label><input type='password' name='password' required><button>Entrar</button></form></div>"))

    def login(self):
        supplied = self.form().get("password", "")
        with db() as con: stored = con.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()[0]
        if not check_password(supplied, stored): return self.admin_login("Senha incorreta.")
        self.redirect_with_cookie("/admin/dashboard", signed_cookie())

    def redirect_with_cookie(self, location, value):
        self.send_response(303); self.send_header("Location", location)
        self.send_header("Set-Cookie", f"wfadmin={value}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800")
        self.end_headers()

    def logout(self): self.redirect_with_cookie("/admin", "deleted; Max-Age=0")

    def dashboard(self, message=""):
        if not self.is_admin(): return self.redirect("/admin")
        with db() as con:
            reqs = con.execute("SELECT * FROM pix_requests ORDER BY id DESC LIMIT 30").fetchall()
            vouchers = con.execute("SELECT * FROM vouchers ORDER BY id DESC LIMIT 20").fetchall()
            sessions = con.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 20").fetchall()
        req_rows = "".join(f"<tr><td>#{r['id']}</td><td>{html.escape(r['client_ip'])}</td><td>{html.escape(r['plan_id'])}<br>{money(r['price_cents'])}</td><td>{html.escape(r['note'] or '')}</td><td>{html.escape(r['status'])}</td><td>{('<form method=post action=/admin/approve><input type=hidden name=id value='+str(r['id'])+'><button class=good>Aprovar</button></form><form method=post action=/admin/reject><input type=hidden name=id value='+str(r['id'])+'><button class=bad>Recusar</button></form>') if r['status']=='pending' else ''}</td></tr>" for r in reqs)
        voucher_rows = "".join(f"<tr><td><b>{html.escape(v['code'])}</b></td><td>{html.escape(v['plan_id'])}</td><td>{v['minutes']} min</td><td>{v['uses']}/{v['max_uses']}</td></tr>" for v in vouchers)
        session_rows = "".join(f"<tr><td>{html.escape(s['client_ip'])}</td><td>{html.escape(s['plan_id'])}</td><td>{dt(s['expires_at'])}</td><td>{html.escape(s['status'])}</td></tr>" for s in sessions)
        options = "".join(f"<option value='{p['id']}'>{html.escape(p['name'])}</option>" for p in CFG["plans"])
        warn = "<div class='msg warn'>Firewall em modo de teste: aprovações criam sessões, mas ainda não alteram a rede.</div>" if not CFG.get("firewall_enabled") else ""
        body = f"""<div class='nav'><a class='btn' href='/'>Portal</a><a class='btn' href='/logout'>Sair</a></div><h1>Painel administrativo</h1>{warn}
        <div class='card'><h2>Solicitações Pix</h2><table><tr><th>ID</th><th>Cliente</th><th>Plano</th><th>Nota</th><th>Status</th><th>Ação</th></tr>{req_rows}</table></div>
        <div class='card'><h2>Gerar código</h2><form method='post' action='/admin/voucher'><label>Plano</label><select name='plan_id'>{options}</select><label>Quantidade de usos</label><input type='number' name='max_uses' min='1' max='20' value='1'><button>Gerar código</button></form><table><tr><th>Código</th><th>Plano</th><th>Duração</th><th>Usos</th></tr>{voucher_rows}</table></div>
        <div class='card'><h2>Sessões</h2><table><tr><th>Cliente</th><th>Plano</th><th>Expira</th><th>Status</th></tr>{session_rows}</table></div>"""
        self.send_html(page("Painel WiFácil", body))

    def approve(self):
        if not self.is_admin(): return self.send_error(403)
        try: request_id = int(self.form().get("id", "0"))
        except ValueError: return self.send_error(400)
        try:
            with db() as con:
                r = con.execute("SELECT * FROM pix_requests WHERE id=? AND status='pending'", (request_id,)).fetchone()
                if r:
                    plan = plan_by_id(r["plan_id"])
                    activate_session(con, r["client_ip"], r["client_mac"], "pix", r["id"], r["plan_id"], plan["minutes"])
                    con.execute("UPDATE pix_requests SET status='approved',decided_at=? WHERE id=?", (now_ts(), request_id))
            self.redirect("/admin/dashboard")
        except Exception as exc: self.send_html(page("Erro", f"<div class='card'><h1>Erro</h1><p>{html.escape(str(exc))}</p><a class='btn' href='/admin/dashboard'>Voltar</a></div>"), 500)

    def reject(self):
        if not self.is_admin(): return self.send_error(403)
        try: request_id = int(self.form().get("id", "0"))
        except ValueError: return self.send_error(400)
        with db() as con: con.execute("UPDATE pix_requests SET status='rejected',decided_at=? WHERE id=? AND status='pending'", (now_ts(), request_id))
        self.redirect("/admin/dashboard")

    def create_voucher(self):
        if not self.is_admin(): return self.send_error(403)
        f = self.form(); plan = plan_by_id(f.get("plan_id", ""))
        if not plan: return self.send_error(400)
        try: max_uses = max(1, min(20, int(f.get("max_uses", "1"))))
        except ValueError: max_uses = 1
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(2))
        with db() as con: con.execute("INSERT INTO vouchers(code,plan_id,minutes,max_uses,created_at) VALUES(?,?,?,?,?)", (code,plan["id"],plan["minutes"],max_uses,now_ts()))
        self.redirect("/admin/dashboard")


if __name__ == "__main__":
    init_db()
    threading.Thread(target=expire_sessions, daemon=True).start()
    server = ThreadingHTTPServer((CFG["bind_host"], int(CFG["port"])), Handler)
    print(f"WiFácil Turbo em http://{CFG['bind_host']}:{CFG['port']}", flush=True)
    server.serve_forever()
