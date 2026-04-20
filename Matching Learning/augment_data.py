import os
from pathlib import Path

import albumentations as A
import cv2

## python "Matching Learning/augment_data.py"

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    source_dir = base_dir / "dataset_final" / "train" / "fondo_vacio"

    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"No se encontro la carpeta: {source_dir.resolve()}")

    transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.RandomBrightnessContrast(p=0.2),
        A.OneOf([
            A.GaussianBlur(blur_limit=(3, 7), p=1.0),
            A.GaussNoise(p=1.0),
        ], p=0.2),
    ])

    image_files = [
        p for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".png"}
    ]

    originals_processed = 0
    generated_count = 0

    for image_path in image_files:
        image = cv2.imread(str(image_path))
        if image is None:
            continue

        originals_processed += 1
        original_name = image_path.stem

        for i in range(1, 5):
            augmented = transform(image=image)["image"]
            output_name = f"aug_{original_name}_{i}.jpg"
            output_path = source_dir / output_name

            # Evita sobreescribir si el script se ejecuta varias veces.
            while output_path.exists():
                i += 1
                output_name = f"aug_{original_name}_{i}.jpg"
                output_path = source_dir / output_name

            cv2.imwrite(str(output_path), augmented)
            generated_count += 1

    print(f"Total de imagenes originales procesadas: {originals_processed}")
    print(f"Total de imagenes nuevas generadas: {generated_count}")


if __name__ == "__main__":
    main()
