import numpy as np
import supervision as sv
from inference import get_model

from src import config


def keep_products(detections: sv.Detections, product_class: str) -> sv.Detections:
    """Drop detections that are not the product class (for example the model's "empty" class)."""
    names = detections.data.get("class_name")
    if names is None or len(detections) == 0:
        return detections
    mask = np.array([str(n).lower() == product_class for n in names])
    return detections[mask]


class ShelfDetector:
    """Wraps the Roboflow model so the rest of the app never touches Inference directly."""

    def __init__(
        self,
        model_id: str,
        api_key: str,
        confidence: float = 0.4,
        product_class: str = config.PRODUCT_CLASS,
    ):
        if not model_id or not api_key:
            raise ValueError("MODEL_ID and ROBOFLOW_API_KEY must be set in your .env file.")
        self.model = get_model(model_id=model_id, api_key=api_key)
        self.confidence = confidence
        self.product_class = product_class

    def detect(self, frame, confidence: float | None = None) -> sv.Detections:
        """Detects products in a BGR frame. `confidence` overrides the default for this call only."""
        result = self.model.infer(
            frame,
            confidence=self.confidence if confidence is None else confidence,
            max_detections=config.MAX_DETECTIONS,
        )[0]
        detections = sv.Detections.from_inference(result)
        return keep_products(detections, self.product_class)
