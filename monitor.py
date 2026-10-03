"""
Monitor de entradas Slipknot (AllAccess) -> aviso por Telegram.

Abre la página con un navegador real (Playwright), llega a "Seleccionar tarifa",
busca "Campo Delantero" y se fija si al lado dice AGOTADO. Si deja de decirlo, te avisa.

Variables de entorno:
  TELEGRAM_TOKEN    token del bot (de @BotFather)          [obligatoria]
  TELEGRAM_CHAT_ID  tu chat id (de @userinfobot)           [obligatoria]
  TICKET_URL        default: la página de Slipknot en AllAccess
  SECTOR            default: Campo Delantero
  WINDOW            caracteres a revisar después del nombre (default: 120)

Uso:
  python monitor.py          # chequea una vez
  python monitor.py --test   # manda un mensaje de prueba a Telegram
  python monitor.py --debug  # muestra qué leyó y guarda captura en debug.png
  python monitor.py --loop   # queda corriendo y chequea cada 3 min (para tu PC)
"""
import os
import random
import re
import sys
import time

import requests
from playwright.sync_api import sync_playwright

URL = os.environ.get("TICKET_URL") or "https://www.allaccess.com.ar/event/slipknot-venta-general"
SECTOR = os.environ.get("SECTOR") or "Campo Delantero"
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WINDOW = int(os.environ.get("WINDOW", "120"))
DEBUG = "--debug" in sys.argv

SOLD_OUT = re.compile(
    r"sold\s*-?\s*out|agotad[oa]s?|sin\s+disponibilidad|no\s+disponible|sin\s+stock",
    re.IGNORECASE,
)
BLOCKED = re.compile(
    r"just a moment|verify you are human|access denied|attention required|"
    r"cloudflare|captcha|403 forbidden|sala de espera|fila virtual|queue-it",
    re.IGNORECASE,
)
# Botones que pueden aparecer antes de llegar a la lista de tarifas
STEP_BUTTONS = ["Comprar", "Comprar entradas", "Ver entradas", "Entradas", "Seleccionar"]


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


def settle(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        pass
    page.wait_for_timeout(3_000)


def sector_visible(page) -> bool:
    return re.search(re.escape(SECTOR), page.inner_text("body"), re.IGNORECASE) is not None


def page_text() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            locale="es-AR",
            viewport={"width": 1280, "height": 1800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
            ),
        )
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        settle(page)

        # Si la lista de tarifas no está a la vista, probar los botones típicos
        for label in STEP_BUTTONS:
            if sector_visible(page):
                break
            btn = page.get_by_role("button", name=re.compile(rf"^\s*{label}\s*$", re.I))
            link = page.get_by_role("link", name=re.compile(rf"^\s*{label}\s*$", re.I))
            for cand in (btn, link):
                if cand.count() > 0:
                    try:
                        cand.first.click(timeout=5_000)
                        settle(page)
                        print(f"[paso] click en '{label}'")
                    except Exception:
                        pass
                    break

        text = page.inner_text("body")
        if DEBUG:
            page.screenshot(path="debug.png", full_page=True)
            print("[debug] captura guardada en debug.png")
        browser.close()
    return text


def check() -> str:
    """Devuelve 'disponible', 'agotado' o 'error'."""
    text = page_text()
    hits = [m.start() for m in re.finditer(re.escape(SECTOR), text, re.IGNORECASE)]

    if not hits:
        if BLOCKED.search(text[:5000]):
            print("AllAccess bloqueó el acceso o hay fila virtual. Probá correrlo desde tu PC.")
        else:
            print(f"No encontré '{SECTOR}'. ¿Cambió la página? Corré con --debug.")
        if DEBUG:
            print(text[:3000])
        return "error"

    # El nombre aparece en la lista y quizás en el mapa. Si CUALQUIER aparición tiene
    # "AGOTADO" al lado, sigue agotado. Solo se avisa si ya no lo dice en ningún lado.
    for i in hits:
        chunk = text[max(0, i - 40) : i + len(SECTOR) + WINDOW]
        if DEBUG:
            print("---\n" + chunk)
        if SOLD_OUT.search(chunk):
            print(f"'{SECTOR}' sigue AGOTADO.")
            return "agotado"

    print("DISPONIBLE")
    telegram(f"🎟️🔥 ¡Se liberaron entradas de {SECTOR} para Slipknot!\nEntrá ya: {URL}")
    return "disponible"


def main() -> int:
    if "--test" in sys.argv:
        telegram(f"✅ Bot funcionando. Te aviso cuando se libere {SECTOR} de Slipknot.")
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
