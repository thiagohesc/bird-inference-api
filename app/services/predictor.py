from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.models import load_model

from app.utils.logger import LoggerConfig

logger = LoggerConfig(
    name="Predictor", log_dir="logs", log_file="Classifier.log"
).get_logger()


@dataclass
class BirdPredictor:
    model_path: Path = Path("data/model.keras")
    classes_path: Path = Path("data/classes.txt")
    img_size: tuple[int, int] = (224, 224)
    _model: Any = field(default=None, init=False, repr=False)
    _class_names: list[str] = field(default_factory=list, init=False, repr=False)
    _load_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def missing_artifacts(self) -> list[str]:
        missing: list[str] = []
        if not self.model_path.exists():
            missing.append(str(self.model_path))
        if not self.classes_path.exists():
            missing.append(str(self.classes_path))
        return missing

    def is_ready(self) -> tuple[bool, list[str]]:
        missing = self.missing_artifacts()
        return (len(missing) == 0, missing)

    def _load_artifacts(self) -> None:
        if self._model is not None and self._class_names:
            return

        with self._load_lock:
            if self._model is not None and self._class_names:
                return

            missing = self.missing_artifacts()
            if missing:
                raise FileNotFoundError(
                    "Artefatos de inferência ausentes: " + ", ".join(missing)
                )

            logger.info(
                "Carregando artefatos de inferência | model=%s classes=%s",
                self.model_path,
                self.classes_path,
            )
            classes_df = pd.read_csv(
                self.classes_path, sep=" ", names=["class_id", "class_name"]
            )
            self._class_names = classes_df.sort_values("class_id")[
                "class_name"
            ].tolist()
            self._model = load_model(self.model_path)
            logger.info("Artefatos de inferência carregados com sucesso.")

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        self._load_artifacts()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize(self.img_size)

        img_array = np.array(image)
        img_array = preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)

        predictions = self._model.predict(img_array, verbose=0)
        predicted_class = int(np.argmax(predictions[0]))
        confidence = float(np.max(predictions[0]))
        predicted_label = self._class_names[predicted_class]

        class_name = re.sub(r"^\d+\.", "", predicted_label)
        class_name = class_name.replace("_", " ")

        return {
            "class_id": predicted_class + 1,
            "class_name": class_name,
            "confidence": round(confidence, 4),
        }
