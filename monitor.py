"""
Monitor de entradas Slipknot (AllAccess) -> aviso por Telegram.

La página pública de AllAccess trae embebido el JSON de la tienda (Crowder) con
cada sector y sus tarifas, y cada tarifa tiene `available` y `max`. No hace falta
login ni pasar la fila virtual: alcanza con bajar el HTML y leer ese JSON.

Ojo: el *sector* "Campo Delantero" figura disponible mientras quede el paquete VIP
(DUALITY EARLY ENTRY, $550.000). Lo que se mira es la *tarifa* común del sector,
la que se llama igual que el sector.

Variables de entorno:
  TELEGRAM_TOKEN    token del bot (de @BotFather)          [obligatoria]
  TELEGRAM_CHAT_ID  tu chat id (de @userinfobot)           [obligatoria]
  TICKET_URL        default: la página de Slipknot en AllAccess
  SECTOR            default: Campo Delantero
  RATE              nombre de la tarifa a vigilar (default: igual a SECTOR)

Uso:
  python monitor.py          # chequea una vez
  python monitor.py --test   # manda un mensaje de prueba a Telegram
  python monitor.py --debug  # lista todos los sectores y tarifas con su estado
  python monitor.py --loop   # queda corriendo y chequea cada 3 min (para tu PC)
"""
import json
import os
import random
import sys
import time

import requests

URL = os.environ.get("TICKET_URL") or "https://www.allaccess.com.ar/event/slipknot-venta-general"
SECTOR = os.environ.get("SECTOR") or "Campo Delantero"
RATE = os.environ.get("RATE") or SECTOR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DEBUG = "--debug" in sys.argv

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def telegram(msg: str) -> None:
    if not TOKEN or not CHAT_ID:
        print("[aviso] Falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID; no se envió:", msg)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True},
        timeout=20,
    )
    print("[telegram]", r.status_code, r.text[:200])


def fetch_shows() -> list:
    """Baja la página y devuelve la lista `shows` del JSON embebido."""
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text
    marker = '"shows":'
    i = html.find(marker + "[")
    if i < 0:
        snippet = html[:300].replace("\n", " ")
        raise RuntimeError(f"No encontré los datos de la tienda (HTTP {r.status_code}): {snippet}")
    shows, _ = json.JSONDecoder().raw_decode(html, i + len(marker))
    return shows


def same(a, b: str) -> bool:
    return (a or "").strip().lower() == b.strip().lower()


def check() -> str:
    """Devuelve 'disponible', 'agotado' o 'error'."""
    try:
        shows = fetch_shows()
    except Exception as e:
        print("[error]", e)
        return "error"

    matches = []
    for show in shows:
        for sector in show.get("sectors") or []:
            if DEBUG:
                print(f"[{show.get('name')}] sector {sector.get('name')!r} available={sector.get('available')}")
            for rate in sector.get("rates") or []:
                if DEBUG:
                    print(
                        f"    tarifa {rate.get('name')!r} ${rate.get('price')} "
                        f"available={rate.get('available')} max={rate.get('max')}"
                    )
                if same(sector.get("name"), SECTOR) and same(rate.get("name"), RATE):
                    matches.append((show, rate))

    if not matches:
        print(f"No encontré la tarifa '{RATE}' en el sector '{SECTOR}'. ¿Cambió la página? Corré con --debug.")
        return "error"

    available = [(s, r) for s, r in matches if r.get("available") or (r.get("max") or 0) > 0]
    if not available:
        print(f"'{RATE}' sigue AGOTADO.")
        return "agotado"

    show, rate = available[0]
    price = f"{rate.get('price') or 0:,}".replace(",", ".")
    print(f"DISPONIBLE: {rate.get('name')} ${price} ({show.get('name')})")
    telegram(
        f"🎟️🔥 ¡Se liberaron entradas de {RATE} para Slipknot!\n"
        f"${price} · {show.get('name')}\n"
        f"Entrá ya: {URL}"
    )
    return "disponible"


def main() -> int:
    if "--test" in sys.argv:
        telegram(f"✅ Bot funcionando. Te aviso cuando se libere {RATE} de Slipknot.")
        return 0

    if "--loop" in sys.argv:
        while True:
            try:
                check()
            except Exception as e:
                print("[error]", e)
            time.sleep(180 + random.randint(0, 60))

    return 1 if check() == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
