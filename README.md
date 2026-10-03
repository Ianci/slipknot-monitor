# Aviso de entradas Slipknot (Campo Delantero) por Telegram

El script ya viene configurado para la página de AllAccess y el sector **Campo Delantero**.
Revisa si sigue apareciendo **AGOTADO** y te escribe por Telegram cuando ese cartel desaparezca.

## 1. Crear el bot (2 min)
1. En Telegram, abrí **@BotFather**, mandá `/newbot` y guardá el **token** que te da.
2. Mandale cualquier mensaje a tu bot nuevo. Si no lo hacés, el bot no puede escribirte.
3. Abrí **@userinfobot** y guardá tu **chat id**.

## 2. Opción A: GitHub Actions (corre solo, sin compu prendida)
1. Creá un repo **público** y subí todo, incluida la carpeta `.github/workflows`.
2. Andá a Settings → Secrets and variables → Actions y cargá `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`.
3. Andá a Actions → "Monitor entradas" → **Run workflow** y mirá el log:
   - `'Campo Delantero' sigue AGOTADO.` significa que funciona. Listo.
   - `AllAccess bloqueó el acceso` significa que bloquean los servidores de GitHub. Usá la opción B.

## 2. Opción B: tu PC (la más confiable con AllAccess)
AllAccess bloquea muchos accesos automáticos desde servidores, pero desde tu conexión de casa suele andar.
```bash
pip install -r requirements.txt
python -m playwright install chromium

# Windows (PowerShell):  $env:TELEGRAM_TOKEN="..."; $env:TELEGRAM_CHAT_ID="..."
export TELEGRAM_TOKEN="..." TELEGRAM_CHAT_ID="..."

python monitor.py --test    # te tiene que llegar un mensaje
python monitor.py --debug   # muestra qué leyó y guarda debug.png
python monitor.py --loop    # queda chequeando cada ~3-4 min
```
Dejá la compu prendida y sin que se suspenda.

## Notas
- Mientras haya entradas disponibles te avisa en cada chequeo, a propósito. Cuando compres,
  cortalo (Ctrl+C en la PC, o Actions → ⋯ → Disable workflow).
- Si dice "No encontré 'Campo Delantero'", corré `--debug` y mirá `debug.png`. Puede que
  la página pida un paso extra (elegir fecha o cantidad) o que esté la fila virtual.
- Solo avisa, no compra. Tené la cuenta de AllAccess logueada y la tarjeta a mano.
