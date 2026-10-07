#!/bin/bash
# Interaktivt valg af sprog til LibreTranslate-modeller.
#
# Brug: ./setup_languages.sh        (eller kaldes automatisk af start.sh)
#
# Vælger man fx dansk og russisk, gemmes "da,en,ru" i langtime.languages,
# og start.sh starter LibreTranslate med --load-only da,en,ru — hvorefter
# KUN de modeller, der forbinder disse sprog, downloades.
# Engelsk tilføjes altid, da modellerne er koblet sammen via engelsk.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$PROJECT_DIR/langtime.languages"

# Sprogkode + navn (hold i tråd med LANGUAGES i app.py)
LANG_OPTIONS=(
    "ru:Russisk"
    "da:Dansk"
    "de:Tysk"
    "fr:Fransk"
    "es:Spansk"
    "it:Italiensk"
    "nl:Hollandsk"
    "pl:Polsk"
    "sv:Svensk"
    "nb:Norsk"
    "fi:Finsk"
    "uk:Ukrainsk"
    "cs:Tjekkisk"
    "pt:Portugisisk"
)

echo "==============================="
echo "  Valg af sprog til LangTime"
echo "==============================="
echo ""
echo "Vælg de sprog, du vil have oversættelsesmodeller til."
echo "(Engelsk tilføjes automatisk, da alle modeller er koblet"
echo " sammen via engelsk — dansk↔russisk kører således som"
echo " dansk↔engelsk↔russisk.)"
echo ""
echo "Indtast numrene adskilt med komma, fx: 1,2"
echo "Skriv 'alle' for at hente ALLE modeller (~10-20 GB!)."
echo ""

i=1
for entry in "${LANG_OPTIONS[@]}"; do
    code="${entry%%:*}"
    name="${entry#*:}"
    printf "  %2d) %-12s (%s)\n" "$i" "$name" "$code"
    i=$((i + 1))
done
echo ""

read -rp "Dit valg: " choice
choice="$(echo "$choice" | tr -d ' ')"

# --- 'alle'-tilfældet: ingen begrænsning ---
if [ "$choice" = "alle" ]; then
    echo "en" > "$CONFIG_FILE"      # kun 'en' = ingen --load-only restriktion... se note
    echo ""
    echo "✓ Alle sprog vil blive hentet (10-20 GB diskplads!)."
    echo "  Fjern filen langtime.languages og kør igen, hvis du"
    echo "  fortryder."
    exit 0
fi

# --- Valider og byg kommasepareret liste ---
SELECTED=""
for num in ${choice//,/ }; do
    if ! [[ "$num" =~ ^[0-9]+$ ]] || [ "$num" -lt 1 ] || [ "$num" -gt ${#LANG_OPTIONS[@]} ]; then
        echo "✗ FEJL: '$num' er ikke et gyldigt nummer."
        exit 1
    fi
    entry="${LANG_OPTIONS[$((num - 1))]}"
    code="${entry%%:*}"
    # undgå dubletter
    if [[ ",$SELECTED," != *",$code,"* ]]; then
        SELECTED="${SELECTED:+$SELECTED,}$code"
    fi
done

if [ -z "$SELECTED" ]; then
    echo "✗ FEJL: Ingen sprog valgt."
    exit 1
fi

# Engelsk som hub — tilføj hvis manglende
if [[ ",$SELECTED," != *",en,"* ]]; then
    SELECTED="$SELECTED,en"
fi

echo "$SELECTED" > "$CONFIG_FILE"

echo ""
echo "✓ Følgende sprog gemt i langtime.languages: $SELECTED"
echo "  (NB: eksisterende modeller på disken genbruges; kun manglende"
echo "   downloades ved næste ./start.sh)"
exit 0