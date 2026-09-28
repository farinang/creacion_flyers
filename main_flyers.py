import pandas as pd

from config.settings import (
    CURRENT_DRIVE_FILE,
    ARCHIVED_DRIVE_FILE
)

from utils.flyer_data import (
    crear_grupos_flyers
)

from utils.flyer import (
    generar_flyers
)


def main():

    print("\n" + "=" * 100)
    print("FASE 3 - GENERACIÓN DE FLYERS")
    print("=" * 100)

    # ========================================================
    # 1. CARGAR DATASETS YA GENERADOS
    # ========================================================

    print("\nCargando datasets...")

    current_drive = pd.read_csv(
        CURRENT_DRIVE_FILE,
        encoding="utf-8-sig"
    )

    archived_drive = pd.read_csv(
        ARCHIVED_DRIVE_FILE,
        encoding="utf-8-sig"
    )

    print(
        f"Current cargadas: "
        f"{len(current_drive)}"
    )

    print(
        f"Archived cargadas: "
        f"{len(archived_drive)}"
    )

    # ========================================================
    # 2. CREAR GRUPOS DE FLYERS
    # ========================================================

    print("\nPreparando grupos...")

    grupos = crear_grupos_flyers(
        current_drive,
        archived_drive
    )

    print(
        f"\nFlyers a generar: "
        f"{len(grupos)}"
    )

    # ========================================================
    # 3. MOSTRAR DISTRIBUCIÓN
    # ========================================================

    for indice, grupo in enumerate(
        grupos,
        start=1
    ):

        current_count = (
            grupo["listing_type"]
            .eq("current")
            .sum()
        )

        archived_count = (
            grupo["listing_type"]
            .eq("archived")
            .sum()
        )

        print(
            f"Flyer {indice}: "
            f"{current_count} Current + "
            f"{archived_count} Archived"
        )

    # ========================================================
    # 4. GENERAR PNG
    # ========================================================

    print("\nGenerando flyers...")

    archivos = generar_flyers(
        grupos
    )

    # ========================================================
    # 5. RESULTADO
    # ========================================================

    print("\n" + "=" * 100)
    print("RESULTADO")
    print("=" * 100)

    for archivo in archivos:

        print(
            f"Generado: "
            f"{archivo}"
        )

    print("\nProceso terminado.")


if __name__ == "__main__":

    main()