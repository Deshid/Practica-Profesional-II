from pathlib import Path

import albumentations as A
import cv2

## python "Matching Learning/balancear_dataset.py"

def _list_images(folder: Path) -> list[Path]:
    valid_ext = {".jpg", ".jpeg", ".png"}
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in valid_ext]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    class_a_dir = base_dir / "dataset_final" / "train" / "objeto_a"
    class_b_dir = base_dir / "dataset_final" / "train" / "fondo_vacio"

    if not class_a_dir.exists() or not class_b_dir.exists():
        raise FileNotFoundError("No se encontraron las carpetas esperadas en dataset_final/train.")

    class_a_images = _list_images(class_a_dir)
    class_b_images = _list_images(class_b_dir)

    class_a_count = len(class_a_images)
    class_b_count = len(class_b_images)

    if class_a_count == class_b_count:
        print(f"Balanceo completado. Clase A: {class_a_count} fotos | Clase B: {class_b_count} fotos")
        return

    if class_a_count > class_b_count:
        minority_dir = class_b_dir
        minority_images = class_b_images
        target_count = class_a_count
    else:
        minority_dir = class_a_dir
        minority_images = class_a_images
        target_count = class_b_count

    if not minority_images:
        raise ValueError("La clase minoritaria no tiene imagenes para aplicar augmentations.")

    to_generate = target_count - len(minority_images)

    transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.5),
        A.Rotate(limit=30, p=0.5),
        A.MultiplicativeNoise(p=0.5),
    ])

    created = 0
    source_index = 0

    while created < to_generate:
        source_path = minority_images[source_index % len(minority_images)]
        source_index += 1

        image = cv2.imread(str(source_path))
        if image is None:
            continue

        augmented = transform(image=image)["image"]

        candidate_idx = created + 1
        output_path = minority_dir / f"balanced_{source_path.stem}_{candidate_idx}.jpg"
        while output_path.exists():
            candidate_idx += 1
            output_path = minority_dir / f"balanced_{source_path.stem}_{candidate_idx}.jpg"

        cv2.imwrite(str(output_path), augmented)
        created += 1

    final_class_a_count = len(_list_images(class_a_dir))
    final_class_b_count = len(_list_images(class_b_dir))
    print(
        f"Balanceo completado. Clase A: {final_class_a_count} fotos | Clase B: {final_class_b_count} fotos"
    )


if __name__ == "__main__":
    main()
