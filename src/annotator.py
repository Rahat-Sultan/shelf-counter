import cv2
import supervision as sv


class Annotator:
    """Draws boxes and a running product count onto a frame."""

    def __init__(self):
        self.box = sv.BoxAnnotator(thickness=2)

    def annotate(self, frame, detections: sv.Detections):
        out = self.box.annotate(scene=frame.copy(), detections=detections)
        cv2.putText(
            out,
            f"Products: {len(detections)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )
        return out
