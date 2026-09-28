from config.settings import (
    PROPERTIES_PER_FLYER
)

from utils.monday import (
    obtener_columnas_disponibles,
    obtener_todos_los_items
)

from utils.inventory import (
    crear_dataframe,
    separar_inventarios,
    guardar_inventarios
)

from utils.drive import (
    conectar_drive
)

from utils.drive_index import (
    construir_indice_drive,
    match_current_drive,
    match_archived_drive,
    calcular_archived_necesarios,
    guardar_drive_datasets,
    auditar_drive_no_utilizado
)

from utils.flyer_data import (
    crear_grupos_flyers
)

from utils.flyer import (
    generar_flyers
)


def main():

    print("\n" + "=" * 100)
    print("RENT REALTY - CREACION DE FLYERS")
    print("=" * 100)

    # ========================================================
    # FASE 1 - MONDAY
    # ========================================================

    print("\nFASE 1 - MONDAY")

    obtener_columnas_disponibles()

    items = (
        obtener_todos_los_items()
    )

    df = (
        crear_dataframe(
            items
        )
    )

    current, archived = (
        separar_inventarios(
            df
        )
    )

    guardar_inventarios(
        current,
        archived
    )

    print("\n" + "=" * 100)
    print("RESUMEN MONDAY")
    print("=" * 100)

    print(
        f"Current detectadas: "
        f"{len(current)}"
    )

    print(
        f"Archived detectadas: "
        f"{len(archived)}"
    )

    # ========================================================
    # FASE 2 - GOOGLE DRIVE
    # ========================================================

    print("\nFASE 2 - GOOGLE DRIVE")

    drive = (
        conectar_drive()
    )

    # ========================================================
    # CREAR ÍNDICE DRIVE UNA SOLA VEZ
    # ========================================================

    drive_index = (
        construir_indice_drive(
            drive
        )
    )

    # ========================================================
    # MATCH CURRENT
    # ========================================================

    current_drive = (
        match_current_drive(
            current,
            drive_index
        )
    )

    # ========================================================
    # CALCULAR ARCHIVED NECESARIOS
    # ========================================================

    archived_necesarios = (
        calcular_archived_necesarios(
            len(current_drive)
        )
    )

    print("\n" + "=" * 100)
    print("CÁLCULO DE FLYERS")
    print("=" * 100)

    print(
        f"Current con imagen: "
        f"{len(current_drive)}"
    )

    print(
        f"Propiedades por flyer: "
        f"{PROPERTIES_PER_FLYER}"
    )

    print(
        f"Archived necesarias para "
        f"completar el último flyer: "
        f"{archived_necesarios}"
    )

    # ========================================================
    # MATCH ARCHIVED
    # ========================================================

    archived_drive = (
        match_archived_drive(
            archived,
            drive_index,
            archived_necesarios
        )
    )

    # ========================================================
    # GUARDAR RESULTADOS DRIVE
    # ========================================================

    guardar_drive_datasets(
        current_drive,
        archived_drive
    )

    auditoria_drive = (
        auditar_drive_no_utilizado(
            drive_index,
            current,
            archived
        )
    )

    # ========================================================
    # RESUMEN DRIVE
    # ========================================================

    print("\n" + "=" * 100)
    print("RESUMEN GOOGLE DRIVE")
    print("=" * 100)

    print(
        f"Current con imagen: "
        f"{len(current_drive)}"
    )

    print(
        f"Archived requeridas: "
        f"{archived_necesarios}"
    )

    print(
        f"Archived encontradas: "
        f"{len(archived_drive)}"
    )

    # print("Aqui muere el main Fase 1 y 2 completado")
    # return

    # ========================================================
    # FASE 3 - PREPARAR FLYERS
    # ========================================================

    print(
        "\nFASE 3 - PREPARANDO FLYERS"
    )

    grupos = (
        crear_grupos_flyers(
            current_drive,
            archived_drive
        )
    )

    print(
        f"\nFlyers a generar: "
        f"{len(grupos)}"
    )

    for indice, grupo in enumerate(
        grupos,
        start=1
    ):

        current_count = (
            grupo[
                "listing_type"
            ]
            .eq("current")
            .sum()
        )

        archived_count = (
            grupo[
                "listing_type"
            ]
            .eq("archived")
            .sum()
        )

        print(
            f"Flyer {indice}: "
            f"{current_count} Current + "
            f"{archived_count} Archived"
        )

    # ========================================================
    # FASE 4 - GENERAR PNG
    # ========================================================

    print(
        "\nFASE 4 - GENERANDO PNG"
    )

    archivos = (
        generar_flyers(
            grupos
        )
    )

    for archivo in archivos:

        print(
            f"Generado: "
            f"{archivo}"
        )

    print(
        "\nProceso terminado."
    )


if __name__ == "__main__":

    main()