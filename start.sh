#!/bin/bash
# LangTime launcher — starter alt med én kommando.
#
# Brug: ./start.sh
#
# Sekvens:
#   1. Tjek/start LibreTranslate ( downloader modeller ved første kørsel —
#      progress vises direkte i terminalen)
#   2. Initialiser databasen
#   3. Start Flask-appen
#   4. Åbn browseren, når siden er klar
#   5. Ctrl+C lukker alt ned pænt

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LT_PORT=5001
APP_PORT=5000
LT_PID=""

cd "$PROJECT_DIR"

# ---------- Hjælpefunktioner ----------

lt_is_running() {
    curl -s --max-time 2 "http://127.0.0.1:$LT_PORT/languages" > /dev/null 2>&1
}

app_is_running() {
    curl -s --max-time 1 "http://127.0.0.1:$APP_PORT" > /dev/null 2>&1
}

cleanup() {
    # Slår LibreTranslate ihjel, hvis VI startede den (og kun da)
    if [ -n "$LT_PID" ] && kill -0 "$LT_PID" 2>/dev/null; then
        echo ""
        echo "Stopper LibreTranslate..."
        kill "$LT_PID" 2>/dev/null
    fi
    echo "Farvel!"
    exit 0
}

# Fang Ctrl+C så cleanup køres
trap cleanup INT TERM

# ---------- 1. LibreTranslate ----------

if lt_is_running; then
    echo "✓ LibreTranslate kører allerede (port $LT_PORT)"
else
    echo "▶ Starter LibreTranslate..."
    echo "  (Første gang downloader den sprogmodeller — det kan tage"
    echo "   flere minutter. Progress vises herunder.)"
    echo ""

    # Baggrundsproces — men STDOUT arver terminalen, så download-
    # progress (modelfiler, procent osv.) vises løbende her.
    "$PROJECT_DIR/lt-env/bin/libretranslate" --port "$LT_PORT" &
    LT_PID=$!

    # Vent til serveren svarer — med synlig tæller
    printf "  Venter på at LibreTranslate bliver klar: "
    ATTEMPTS=0
    until lt_is_running; do
        ATTEMPTS=$((ATTEMPTS + 1))
        if [ $ATTEMPTS -ge 120 ]; then
            echo ""
            echo "✗ FEJL: LibreTranslate svarede ikke efter 120 sekunder."
            echo "  Kig i outputtet ovenfor efter fejlbeskeder."
            cleanup
        fi
        # Status prik hvert 2. sekund —LT-downloads fortsætter med
        # at skrive deres egne linjer imellem
        printf "."
        sleep 2
    done
    echo ""
    echo "✓ LibreTranslate er klar (port $LT_PORT)"
fi

# ---------- 2. Databasen ----------

echo "▶ Initialiserer databasen..."
"$PROJECT_DIR/.venv/bin/python" -c "from db import init_db; init_db()"
echo "✓ Databasen er klar"

# ---------- 3. Browser (venter på appen, åbner når den er klar) ----------

# Lille baggrunds-job: venter på Flask og åbner derefter browseren.
# Kører parallelt med, at vi starter appen herunder — ingen spildtid.
(
    ATTEMPTS=0
    until app_is_running; do
        ATTEMPTS=$((ATTEMPTS + 1))
        [ $ATTEMPTS -ge 20 ] && exit 1   # opgiv stille, hvis appen ikke starter
        sleep 1
    done
    xdg-open "http://127.0.0.1:$APP_PORT" > /dev/null 2>&1 &
) &

# ---------- 4. Flask-appen (forgrund — Ctrl+C stopper her) ----------

echo "▶ Starter LangTime på http://127.0.0.1:$APP_PORT ..."
echo ""
"$PROJECT_DIR/.venv/bin/python" app.py

# Når appen lukker (Ctrl+C), ryd op bag os
cleanup