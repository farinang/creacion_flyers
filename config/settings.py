from pathlib import Path


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"

DATA_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)


# ============================================================
# MONDAY
# ============================================================

MONDAY_API_URL = "https://api.monday.com/v2"

BOARD_ID = 18415696704


# ============================================================
# TOKEN MONDAY
# ============================================================

MONDAY_TOKEN_FILE = (
    CREDENTIALS_DIR /
    "monday_token.txt"
)


def leer_monday_token():

    if not MONDAY_TOKEN_FILE.exists():

        raise FileNotFoundError(
            f"No existe:\n{MONDAY_TOKEN_FILE}"
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


# ============================================================
# COLUMNAS DATASET
# ============================================================

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
# ARCHIVOS
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
    "1kYW8-FKzeGeNuuuKbIBCbZ5DJEkV9vd2"
)


GOOGLE_SERVICE_ACCOUNT_FILE = (
    CREDENTIALS_DIR /
    "google_service_account.json"
)

GOOGLE_DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]


# ============================================================
# ARCHIVED
# ============================================================

# Máximo número de propiedades rentadas que podrían
# necesitarse para completar un flyer
MAX_ARCHIVED_IMAGES = 9

# Máximo número de propiedades Archived que se revisarán
# para intentar conseguir esas imágenes
MAX_ARCHIVED_SEARCH_ATTEMPTS = (
    MAX_ARCHIVED_IMAGES * 2
)