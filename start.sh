#!/bin/bash
# LangTime launcher — starter alt med én kommando.
#
# Brug: ./start.sh
#
# Sekvens:
#   0. Tjek at systemafhængigheder (python3, pip, venv, curl) er på plads
#   1. Opret .venv og lt-env hvis de mangler (med brugerens samtykke)
#   2. Tjek/start LibreTranslate (downloader modeller ved første kørsel —
#      progress vises direkte i terminalen)
#   3. Initialiser databasen
#   4. Start Flask-appen
#   5. Åbn browseren, når siden er klar
#   6. Ctrl+C lukker alt ned pænt

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LT_PORT=5001
APP_PORT=5000
LT_PID=""

cd "$PROJECT_DIR"

# ---------- Hjælpefunktioner ----------

print_error() {
    echo "✗ FEJL: $1"
}

print_warning() {
    echo "⚠ VARSEL: $1"
}

print_success() {
    echo "✓ $1"
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

# ---------- Trin 0a: System-afhængigheder ----------

check_dependencies() {
    local errors_found=0

    echo "▶ Tjekker system-afhængigheder..."
    echo ""

    # 1. Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 er ikke installeret."
        echo "   Installer med:"
        echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        echo "   macOS: brew install python3"
        echo "   Fedora: sudo dnf install python3 python3-pip"
        echo ""
        errors_found=1
    else
        print_success "Python3 fundet ($(python3 --version))"
    fi

    # 2. Pip
    if ! command -v pip3 &> /dev/null; then
        if ! python3 -m pip --version &> /dev/null; then
            print_error "pip er ikke installeret."
            echo "   Installer med: sudo apt install python3-pip"
            echo ""
            errors_found=1
        else
            print_success "pip fundet (via python3 -m pip)"
        fi
    else
        print_success "pip3 fundet"
    fi

    # 3. venv-support — den eneste pålidelige test er at skabe et venv
    if [ -n "$(command -v python3)" ]; then
        VENV_TEST_DIR="$(mktemp -d)"
        if python3 -m venv "$VENV_TEST_DIR/probe" &> /dev/null; then
            print_success "venv-understøttelse fundet"
        else
            print_error "venv-module mangler (python3-venv)."
            echo "   Installer med: sudo apt install python3-venv"
            echo "   (på Ubuntu 24.04 hedder den python3.12-venv)"
            echo ""
            errors_found=1
        fi
        rm -rf "$VENV_TEST_DIR"
    fi

    # 4. curl (til health-checks)
    if ! command -v curl &> /dev/null; then
        print_error "curl er ikke installeret."
        echo "   Installer med: sudo apt install curl"
        echo ""
        errors_found=1
    else
        print_success "curl fundet"
    fi

    # 5. xdg-open (til browser-åbning) — kun en advarsel
    if ! command -v xdg-open &> /dev/null; then
        print_warning "xdg-open mangler (kan ikke åbne browser automatisk)."
        echo "   Installer med: sudo apt install xdg-utils"
        echo "   Eller åbn browseren manuelt på http://127.0.0.1:$APP_PORT"
        echo ""
    fi

    echo ""
    return $errors_found
}

# ---------- Trin 0b: Virtuelle miljøer (oprettes automatisk hvis de mangler) ----------

setup_venvs() {
    local missing=0

    if [ ! -d ".venv" ]; then
        echo "▶ Appens virtuelle miljø (.venv) findes ikke."
        missing=1
    fi

    if [ ! -d "lt-env" ]; then
        echo "▶ LibreTranslate-miljøet (lt-env) findes ikke."
        missing=1
    fi

    if [ $missing -eq 0 ]; then
        print_success ".venv og lt-env fundet"
        echo ""
        return 0
    fi

    echo ""
    read -rp "Vil du opbygge de manglende miljøer nu? [J/n] " answer
    case "$answer" in
        [nN]*)
            echo "Okay — gør det manuelt med kommandoerne fra README'en og kør ./start.sh igen."
            exit 1
            ;;
    esac

    if [ ! -d ".venv" ]; then
        echo "▶ Opretter .venv og installerer app-afhængigheder..."
        if ! python3 -m venv .venv; then
            print_error "Kunne ikke oprette .venv"
            exit 1
        fi
        if ! "$PROJECT_DIR/.venv/bin/pip" install -r requirements.txt; then
            print_error "pip-install fejlede i .venv"
            exit 1
        fi
        print_success ".venv er klar"
    fi

    if [ ! -d "lt-env" ]; then
        echo "▶ Opretter lt-env og installerer LibreTranslate (tager flere minutter)..."
        if ! python3 -m venv lt-env; then
            print_error "Kunne ikke oprette lt-env"
            exit 1
        fi
        if ! "$PROJECT_DIR/lt-env/bin/pip" install libretranslate; then
            print_error "pip-install fejlede i lt-env"
            exit 1
        fi
        print_success "lt-env er klar"
    fi

    echo ""
    return 0
}

# ---------- Health-checks ----------

lt_is_running() {
    curl -s --max-time 2 "http://127.0.0.1:$LT_PORT/languages" > /dev/null 2>&1
}

app_is_running() {
    curl -s --max-time 1 "http://127.0.0.1:$APP_PORT" > /dev/null 2>&1
}

# ==================== START HER ====================

if ! check_dependencies; then
    echo "❌ SYSTEM-AFHÆNGIGHEDER MANGLER. Installér dem og kør ./start.sh igen."
    exit 1
fi

setup_venvs

# ---------- 1. LibreTranslate ----------

if lt_is_running; then
    print_success "LibreTranslate kører allerede (port $LT_PORT)"
else
    echo "▶ Starter LibreTranslate..."
    echo "  (Første gang downloader den sprogmodeller — det kan tage"
    echo "   længere tid. Progress vises herunder.)"
    echo ""

    # Baggrundsproces — STDOUT arver terminalen, så download-
    # progress vises løbende her.
    "$PROJECT_DIR/lt-env/bin/libretranslate" --port "$LT_PORT" &
    LT_PID=$!

    printf "  Venter på at LibreTranslate bliver klar: "
    ATTEMPTS=0
    TIMEOUT_MINUTES=60        # maks. ventetid i minutter
    SECONDS_PER_TRY=2         # hvert forsøg tager ~2 sekunder
    MAX_ATTEMPTS=$((TIMEOUT_MINUTES * 60 / SECONDS_PER_TRY))

    until lt_is_running; do
        ATTEMPTS=$((ATTEMPTS + 1))
        if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
            echo ""
            print_error "LibreTranslate svarede ikke efter $TIMEOUT_MINUTES minutter."
            echo "  Hvis der lige er downloadet sprogmodeller ovenfor, er der måske"
            echo "  sket en netværksafbrydelse — kør ./start.sh igen; download"
            echo "  genoptages hvor den slap."
            cleanup
        fi
        printf "."
        sleep $SECONDS_PER_TRY
    done
    echo ""
    print_success "LibreTranslate er klar (port $LT_PORT)"
fi

# ---------- 2. Databasen ----------

echo "▶ Initialiserer databasen..."
"$PROJECT_DIR/.venv/bin/python" -c "from db import init_db; init_db()"
print_success "Databasen er klar"

# ---------- 3. Browser (venter på appen, åbner når den er klar) ----------

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