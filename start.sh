#!/bin/bash
# LangTime launcher — starter alt med én kommando.
#
# Brug: ./start.sh
#
# Sekvens:
#   1. Tjek om alle dependencies er på plads
#   2. Tjek/start LibreTranslate ( downloader modeller ved første kørsel —
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

# ---------- FUNKTION: Check og ret dependencies ----------

print_error() {
    echo "✗ FEJL: $1"
}

print_warning() {
    echo "⚠ VARSEL: $1"
}

print_success() {
    echo "✓ $1"
}

check_dependencies() {
    local errors_found=0

    echo "▶ Tjekker dependencies..."
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
        # Fallback: tjek om pip findes via python3 -m pip
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

    # 3. venv-support
    if [ -n "$(command -v python3)" ]; then
        if ! python3 -m venv --version &> /dev/null; then
            print_error "venv-module mangler (python3-venv)."
            echo "   Installer med: sudo apt install python3-venv"
            echo ""
            errors_found=1
        else
            print_success "venv-understøttelse fundet"
        fi
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

    # 5. xdg-open (til browser-åbning på Linux)
    if ! command -v xdg-open &> /dev/null; then
        print_warning "xdg-open mangler (kan ikke åbne browser automatisk)."
        echo "   Installer med: sudo apt install xdg-utils"
        echo "   Eller åbn browseren manuelt på http://127.0.0.1:$APP_PORT"
        echo ""
    fi

    echo ""

    return $errors_found
}

# 6. Tjek om .venv eksisterer
check_venvs() {
    local errors_found=0

    if [ ! -d ".venv" ]; then
        print_error "Appens virtuelle miljø (.venv) mangler."
        echo "   Opret det med:"
        echo "   python3 -m venv .venv"
        echo "   source .venv/bin/activate"
        echo "   pip install -r requirements.txt"
        echo ""
        errors_found=1
    else
        print_success ".venv fundet"
    fi

    if [ ! -d "lt-env" ]; then
        print_error "LibreTranslate-miljø (lt-env) mangler."
        echo "   Opret det med:"
        echo "   python3 -m venv lt-env"
        echo "   source lt-env/bin/activate"
        echo "   pip install libretranslate"
        echo ""
        errors_found=1
    else
        print_success "lt-env fundet"
    fi

    echo ""
    return $errors_found
}

# ---------- FUNKTION: Cleanup ----------

cleanup() {
    if [ -n "$LT_PID" ] && kill -0 "$LT_PID" 2>/dev/null; then
        echo ""
        echo "Stopper LibreTranslate..."
        kill "$LT_PID" 2>/dev/null
    fi
    echo "Farvel!"
    exit 0
}

trap cleanup INT TERM

# ---------- HAVNEFJORD: Kør checks ----------

if ! check_dependencies; then
    echo "❌ INSTALLATION IKKE KLAR. Installér de manglende dependencies og prøv igen."
    exit 1
fi

if ! check_venvs; then
    echo "❌ VIRTUAL ENVIRONMENTS IKKE KLAR. Opret dem og prøv igen."
    exit 1
fi

# ---------- HJÆLPEFUNKTIONER ----------

lt_is_running() {
    curl -s --max-time 2 "http://127.0.0.1:$LT_PORT/languages" > /dev/null 2>&1
}

app_is_running() {
    curl -s --max-time 1 "http://127.0.0.1:$APP_PORT" > /dev/null 2>&1
}

# ---------- 1. LibreTranslate ----------

if lt_is_running; then
    print_success "LibreTranslate kører allerede (port $LT_PORT)"
else
    echo "▶ Starter LibreTranslate..."
    echo "  (Første gang downloader den sprogmodeller — det kan tage"
    echo "   flere minutter. Progress vises herunder.)"
    echo ""

    "$PROJECT_DIR/lt-env/bin/libretranslate" --port "$LT_PORT" &
    LT_PID=$!

    printf "  Venter på at LibreTranslate bliver klar: "
    ATTEMPTS=0
    until lt_is_running; do
        ATTEMPTS=$((ATTEMPTS + 1))
        if [ $ATTEMPTS -ge 120 ]; then
            echo ""
            print_error "LibreTranslate svarede ikke efter 120 sekunder."
            echo "  Kig i outputtet ovenfor efter fejlbeskeder."
            cleanup
        fi
        printf "."
        sleep 2
    done
    echo ""
    print_success "LibreTranslate er klar (port $LT_PORT)"
fi

# ---------- 2. Databasen ----------

echo "▶ Initialiserer databasen..."
"$PROJECT_DIR/.venv/bin/python" -c "from db import init_db; init_db()"
print_success "Databasen er klar"

# ---------- 3. Browser ----------

(
    ATTEMPTS=0
    until app_is_running; do
        ATTEMPTS=$((ATTEMPTS + 1))
        [ $ATTEMPTS -ge 20 ] && exit 1
        sleep 1
    done
    xdg-open "http://127.0.0.1:$APP_PORT" > /dev/null 2>&1 &
) &

# ---------- 4. Flask-appen ----------

echo "▶ Starter LangTime på http://127.0.0.1:$APP_PORT ..."
echo ""
"$PROJECT_DIR/.venv/bin/python" app.py

cleanup