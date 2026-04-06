import argparse
import random
import re
import shutil
from pathlib import Path

PATRON_ARCHIVO = re.compile(r"^(?P<disparo>\d+)_c\d+\.(jpg|jpeg|png|bmp)$", re.IGNORECASE)

## comando de ejemplo para ejecutar el script:
## python "Matching Learning/organizar_dataset.py" --dataset "Matching Learning/dataset" --salida "Matching Learning/dataset_final" --seed 42

def obtener_clases(dataset_dir: Path):
    return [p for p in sorted(dataset_dir.iterdir()) if p.is_dir()]


def agrupar_por_disparo(carpeta_clase: Path):
    grupos = {}

    for archivo in sorted(carpeta_clase.iterdir()):
        if not archivo.is_file():
            continue

        coincidencia = PATRON_ARCHIVO.match(archivo.name)
        if not coincidencia:
            continue

        disparo_id = coincidencia.group("disparo")
        grupos.setdefault(disparo_id, []).append(archivo)

    return grupos


def dividir_grupos(ids_disparo, proporcion_train=0.70, proporcion_val=0.15):
    total = len(ids_disparo)
    n_train = int(total * proporcion_train)
    n_val = int(total * proporcion_val)
    n_test = total - n_train - n_val

    train_ids = ids_disparo[:n_train]
    val_ids = ids_disparo[n_train:n_train + n_val]
    test_ids = ids_disparo[n_train + n_val:n_train + n_val + n_test]

    return {
        "train": train_ids,
        "val": val_ids,
        "test": test_ids,
    }


def copiar_grupos(grupos, ids_por_split, clase, dataset_final_dir: Path):
    resumen = {
        "train": 0,
        "val": 0,
        "test": 0,
    }

    for split, ids in ids_por_split.items():
        destino_clase = dataset_final_dir / split / clase
        destino_clase.mkdir(parents=True, exist_ok=True)

        for disparo_id in ids:
            for archivo in grupos[disparo_id]:
                shutil.copy2(archivo, destino_clase / archivo.name)
                resumen[split] += 1

    return resumen


def organizar_dataset(dataset_dir: Path, dataset_final_dir: Path, seed: int | None = None):
    if not dataset_dir.exists() or not dataset_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de dataset: {dataset_dir}")

    if dataset_final_dir.exists():
        raise FileExistsError(
            f"La carpeta destino ya existe: {dataset_final_dir}. "
            "Eliminala manualmente o usa otra ruta de salida."
        )

    clases = obtener_clases(dataset_dir)
    if not clases:
        raise ValueError(f"No se encontraron subcarpetas de clase en: {dataset_dir}")

    rng = random.Random(seed)

    resumen_global = {
        "train": 0,
        "val": 0,
        "test": 0,
    }

    for carpeta_clase in clases:
        grupos = agrupar_por_disparo(carpeta_clase)
        ids_disparo = list(grupos.keys())

        if not ids_disparo:
            print(f"Aviso: la clase '{carpeta_clase.name}' no tiene archivos validos, se omite.")
            continue

        rng.shuffle(ids_disparo)
        ids_por_split = dividir_grupos(ids_disparo)
        resumen_clase = copiar_grupos(grupos, ids_por_split, carpeta_clase.name, dataset_final_dir)

        resumen_global["train"] += resumen_clase["train"]
        resumen_global["val"] += resumen_clase["val"]
        resumen_global["test"] += resumen_clase["test"]

        print(
            f"Clase '{carpeta_clase.name}': "
            f"train={resumen_clase['train']} | "
            f"val={resumen_clase['val']} | "
            f"test={resumen_clase['test']}"
        )

    print("\nResumen global de imagenes:")
    print(f"train: {resumen_global['train']}")
    print(f"val:   {resumen_global['val']}")
    print(f"test:  {resumen_global['test']}")


def main():
    parser = argparse.ArgumentParser(
        description="Organiza dataset por clase en train/val/test sin separar camaras del mismo disparo."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("dataset"),
        help="Ruta de entrada con subcarpetas por clase (default: dataset)",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("dataset_final"),
        help="Ruta de salida para train/val/test (default: dataset_final)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla para mezcla reproducible de disparos (default: 42)",
    )

    args = parser.parse_args()

    organizar_dataset(args.dataset, args.salida, args.seed)


if __name__ == "__main__":
    main()
