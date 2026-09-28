from pathlib import Path


# ============================================================
# RUTAS BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"

FLYERS_DIR = OUTPUT_DIR / "flyers"


# ============================================================
# CREAR CARPETAS SI NO EXISTEN
# ============================================================

DATA_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)
ICONS_DIR.mkdir(exist_ok=True)

FLYERS_DIR.mkdir(exist_ok=True)


# ============================================================
# MONDAY
# ============================================================

MONDAY_API_URL = "https://api.monday.com/v2"

BOARD_ID = 18415696704


MONDAY_TOKEN_FILE = (
    CREDENTIALS_DIR /
    "monday_token.txt"
)


def leer_monday_token():

    if not MONDAY_TOKEN_FILE.exists():

        raise FileNotFoundError(
            f"No existe:\n"
            f"{MONDAY_TOKEN_FILE}"
        )

    token = (
        MONDAY_TOKEN_FILE
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )

    if not token:

        raise ValueError(
            "El token de Monday está vacío."
        )

    return token


MONDAY_TOKEN = leer_monday_token()


# ============================================================
# COLUMNAS MONDAY
# ============================================================

MONDAY_COLUMNS = {

    "Bedroom":
        "color_mm3xssw2",

    "Bath":
        "color_mm3xmjhf",

    "Phase":
        "color_mm3xxfy2",

    "Price":
        "numeric_mm3xnfb9",

    "Date Listed":
        "date_mm6t5jrt",

    "Reminder Date":
        "date_mm5am4jg",

    "Status":
        "status",

    "Assigned":
        "multiple_person_mm3x4ht9",

    "Access":
        "text_mm3x50vh",

    "Vacancy date":
        "date_mm5avryw",

    "Details":
        "text_mm3xc81j",

    "Location":
        "color_mm3x1k0s",

    "Rented":
        "color_mm3xb3a0",

    "Rented Date":
        "date_mm5akp4q",

    "Last updated":
        "pulse_updated_mm5836zb"
}


OUTPUT_COLUMNS = [

    "property",
    "Status",
    "Assigned",
    "Bedroom",
    "Bath",
    "Price",
    "Date Listed",
    "Reminder Date",
    "Access",
    "Vacancy date",
    "Details",
    "Phase",
    "Location",
    "Rented",
    "Rented Date",
    "Last updated"
]


# ============================================================
# PHASES
# ============================================================

PHASE_CURRENT = "Current"
PHASE_ARCHIVED = "Archived"


# ============================================================
# ARCHIVOS CSV
# ============================================================

CURRENT_INVENTORY_FILE = (
    DATA_DIR /
    "current_inventory.csv"
)

ARCHIVED_INVENTORY_FILE = (
    DATA_DIR /
    "archived_inventory.csv"
)

CURRENT_DRIVE_FILE = (
    DATA_DIR /
    "current_inventory_drive.csv"
)

ARCHIVED_DRIVE_FILE = (
    DATA_DIR /
    "archived_inventory_drive.csv"
)


# ============================================================
# GOOGLE DRIVE
# ============================================================

DRIVE_ROOT_FOLDER_ID = (
    "1vDvq0L8dagFpi-OIFwdj1rFVEgYIQv4U"
)


GOOGLE_API_KEY_FILE = (
    CREDENTIALS_DIR /
    "google_api_key.txt"
)


def leer_google_api_key():

    if not GOOGLE_API_KEY_FILE.exists():

        raise FileNotFoundError(
            f"No existe:\n"
            f"{GOOGLE_API_KEY_FILE}"
        )

    api_key = (
        GOOGLE_API_KEY_FILE
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )

    if not api_key:

        raise ValueError(
            "La API Key de Google está vacía."
        )

    return api_key


GOOGLE_API_KEY = (
    leer_google_api_key()
)


# ============================================================
# FLYER - LÓGICA GENERAL
# ============================================================

PROPERTIES_PER_FLYER = 10

FLYER_COLUMNS = 2
FLYER_ROWS = 5


# ============================================================
# FLYER - TAMAÑO
# ============================================================

FLYER_WIDTH = 830
FLYER_HEIGHT = 1350


# ============================================================
# FLYER - COLORES
# ============================================================

COLOR_BLUE = "#0070AB"
COLOR_WHITE = "#FFFFFF"
COLOR_GOLD = "#BAA361"
COLOR_ORANGE = "#FA8C00"


# ============================================================
# FLYER - TEMPLATE BASE
# ============================================================

FLYER_TEMPLATE_FILE = (
    TEMPLATES_DIR /
    "flyer_base.png"
)


# ============================================================
# FLYER - ÍCONOS
# ============================================================

BED_ICON_FILE = (
    ICONS_DIR /
    "bed.png"
)

BATH_ICON_FILE = (
    ICONS_DIR /
    "bath.png"
)


# ============================================================
# FLYER - FUENTES
# ============================================================

FONT_GARET_BOLD = (
    FONTS_DIR /
    "DejaVuSans-Bold.ttf"
)

FONT_GARET_REGULAR = (
    FONTS_DIR /
    "Garet Book 300.ttf"
)

FONT_COMFORTAA_BOLD = (
    FONTS_DIR /
    "Comfortaa-Bold.ttf"
)

FONT_LEAGUE_SPARTAN_BOLD = (
    FONTS_DIR /
    "League Spartan Bold 700.otf"
)


# ============================================================
# FLYER - TAMAÑOS DE FUENTE
# ============================================================

# ============================================================
# FLYER - TAMAÑOS DE FUENTE
# ============================================================

FONT_SIZE_LOCATION = 22

# Tamaño mínimo permitido cuando Location
# es una sola palabra y no cabe en su ancho máximo
FONT_SIZE_LOCATION_MIN = 15

FONT_SIZE_PRICE = 16
FONT_SIZE_BADGE = 8

FONT_SIZE_BED_BATH_VALUE = 11
FONT_SIZE_BED_BATH_LABEL = 11

FONT_SIZE_RENTED = 40


# ============================================================
# FLYER - GRID GENERAL
# ============================================================

GRID_TOP = 210

GRID_LEFT_X = 70
GRID_RIGHT_X = 425

GRID_ROW_HEIGHT = 158
GRID_ROW_GAP = 6


# ============================================================
# FLYER - IMÁGENES
# ============================================================

PROPERTY_IMAGE_WIDTH = 220
PROPERTY_IMAGE_HEIGHT = 145


# ============================================================
# FLYER - CONTENEDORES DE PROPIEDAD
# ============================================================
#
# IMPORTANTE:
#
# La IZQUIERDA es el layout MAESTRO.
#
# La DERECHA se calcula automáticamente
# haciendo un MIRROR horizontal.
#
# Por lo tanto, cualquier cambio que hagamos
# en los valores LEFT_... se reflejará
# automáticamente en el lado derecho.
#
# ============================================================


# ============================================================
# ANCHO TOTAL DE UNA CARD
# ============================================================
#
# Este ancho permite hacer el espejo.
#
# IZQUIERDA:
#
# INFO | FOTO
#
# DERECHA:
#
# FOTO | INFO
#
# ============================================================

PROPERTY_CARD_WIDTH = 335

PROPERTY_CARD_HEIGHT = 145


# ============================================================
# IMAGEN - LAYOUT MAESTRO IZQUIERDA
# ============================================================

LEFT_IMAGE_X_OFFSET = 115
LEFT_IMAGE_Y_OFFSET = 0


# ============================================================
# CONTENEDOR INFO - LAYOUT MAESTRO IZQUIERDA
# ============================================================

LEFT_INFO_GROUP_X_OFFSET = 0
LEFT_INFO_GROUP_Y_OFFSET = 3

LEFT_INFO_GROUP_WIDTH = 110
LEFT_INFO_GROUP_HEIGHT = 145


# ============================================================
# LOCATION - IZQUIERDA
# ============================================================

LEFT_LOCATION_REL_X = 0
LEFT_LOCATION_REL_Y = 20


# ============================================================
# BADGE FOR RENT - IZQUIERDA
# ============================================================

LEFT_BADGE_REL_X = 41
LEFT_BADGE_REL_Y = 48


# ============================================================
# PRICE - IZQUIERDA
# ============================================================

LEFT_PRICE_REL_X = 5
LEFT_PRICE_REL_Y = 65


# ============================================================
# BED / BATH - IZQUIERDA
# ============================================================
#
# IZQUIERDA:
#
# BED | BATH | FOTO
#
# BATH es el elemento más cercano a la foto.
#
# Estos valores parten exactamente de tu layout actual:
#
# Bed  = X 10
# Bath = X 10 + 52 + separación
#
# ============================================================

LEFT_FEATURE_FAR_REL_X = 10

# Separación entre el bloque Bed y Bath
BED_BATH_GAP = 0

LEFT_FEATURE_NEAR_REL_X = (
    LEFT_FEATURE_FAR_REL_X
    + 52
    + BED_BATH_GAP
)

LEFT_FEATURE_Y = 110

# ============================================================
# ANCHO CONCEPTUAL DE CADA FEATURE
# ============================================================
#
# Solo se utiliza para calcular el mirror.
#
# NO cambia el tamaño real de los íconos.
#
# ============================================================

FEATURE_SLOT_WIDTH = 40

# ============================================================
# AJUSTE FINO DETAILS - DERECHA
# ============================================================
#
# Corrige horizontalmente todo el bloque Bed/Bath
# del lado derecho después de hacer el mirror.
#
# Negativo = mueve hacia la izquierda / hacia la foto
# Positivo = mueve hacia la derecha
#
# ============================================================

RIGHT_DETAILS_OFFSET_X = -4

# Ajuste vertical opcional
RIGHT_DETAILS_OFFSET_Y = 0

# ============================================================
# FLYER - BADGE FOR RENT
# ============================================================

FOR_RENT_TEXT = "For Rent"

FOR_RENT_BADGE_WIDTH = 67
FOR_RENT_BADGE_HEIGHT = 11

FOR_RENT_BADGE_RADIUS = (
    FOR_RENT_BADGE_HEIGHT // 2
)

FOR_RENT_BG_COLOR = COLOR_GOLD
FOR_RENT_TEXT_COLOR = COLOR_WHITE


# ============================================================
# FLYER - RENTED
# ============================================================

RENTED_TEXT = "RENTED"

RENTED_TEXT_COLOR = COLOR_ORANGE

RENTED_ANGLE = 18


# ============================================================
# FLYER - PRICE BOX
# ============================================================

PRICE_BOX_WIDTH = 145
PRICE_BOX_HEIGHT = 35

PRICE_BOX_RADIUS = (
    PRICE_BOX_HEIGHT // 2
)

PRICE_BOX_FILL = COLOR_WHITE
PRICE_BOX_OUTLINE = COLOR_GOLD

PRICE_TEXT_COLOR = COLOR_BLUE


# ============================================================
# FLYER - BED / BATH
# ============================================================

BED_BATH_ICON_SIZE = 13

BED_BATH_TEXT_COLOR = COLOR_WHITE

BED_BATH_ICON_COLOR = COLOR_GOLD


# ============================================================
# BED / BATH - ESPACIADO INTERNO
# ============================================================

# Distancia horizontal entre icono y número
FEATURE_ICON_VALUE_GAP = 5

# Distancia vertical entre número y texto Bed/Bath
FEATURE_VALUE_LABEL_GAP = 7

# Ajuste vertical del icono
FEATURE_ICON_Y_OFFSET = 2


# ============================================================
# FLYER - LOCATION
# ============================================================

LOCATION_TEXT_COLOR = COLOR_WHITE

LOCATION_MAX_WIDTH_LEFT = 110
LOCATION_MAX_WIDTH_RIGHT = 110

LOCATION_MAX_LINES = 2

# Cuántos píxeles adicionales subir
# cuando Location ocupa 2 líneas
LOCATION_MULTILINE_EXTRA_UP = 12

# ============================================================
# FLYER - SALIDA
# ============================================================

FLYER_FILE_PREFIX = "weekly_listing"

FLYER_FORMAT = "PNG"


# ============================================================
# TEXTOS FIJOS
# ============================================================

FLYER_TITLE = "Weekly Listing Page"

FOOTER_TEXT = (
    "Wide selection of\n"
    "properties, Find your\n"
    "perfect match!"
)

CONTACT_TITLE = "Contact Us Today"

CONTACT_NAMES = (
    "Zeke Wigder | Shlomy Friedman"
)

CONTACT_PHONE = "845.410.2077"