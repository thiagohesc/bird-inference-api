import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.services.predictor import BirdPredictor
from app.utils.logger import LoggerConfig
from app.utils.utils_s3 import download_inference_artifacts_from_env

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

logger = LoggerConfig(
    name="InferenceAPI", log_dir="logs", log_file="InferenceAPI.log"
).get_logger()

MODEL_PATH = Path(os.getenv("MODEL_PATH", "app/data/model.keras"))
CLASSES_PATH = Path(os.getenv("CLASSES_PATH", "app/data/classes.txt"))


predictor = BirdPredictor(
    model_path=MODEL_PATH,
    classes_path=CLASSES_PATH,
)


@app.on_event("startup")
def startup_download_artifacts() -> None:
    try:
        downloaded = download_inference_artifacts_from_env(
            model_dest=MODEL_PATH,
            classes_dest=CLASSES_PATH,
            overwrite=False,
        )
        logger.info(
            "Artefatos prontos para inferência | model=%s classes=%s",
            downloaded[0],
            downloaded[1],
        )
    except Exception:
        logger.exception("Falha ao baixar artefatos de inferência do S3.")
        raise


@app.get("/health")
def health():
    ready, missing = predictor.is_ready()
    return {
        "status": "ok" if ready else "waiting_artifacts",
        "missing_artifacts": missing,
    }


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")

    try:
        image_bytes = await file.read()
        prediction = predictor.predict(image_bytes)
        return JSONResponse(content=prediction)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
