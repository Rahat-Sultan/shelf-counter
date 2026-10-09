import cv2
import supervision as sv


class Annotator:
    """Draws boxes and a running product count onto a frame."""

    def annotate(self, frame, detections: sv.Detections):
        height, width = frame.shape[:2]
        # Scale lines and text with the image so small, dense photos are not buried under boxes.
        thickness = sv.calculate_optimal_line_thickness(resolution_wh=(width, height))
        out = sv.BoxAnnotator(thickness=thickness).annotate(scene=frame.copy(), detections=detections)
        self._draw_count(out, len(detections))
        return out

    @staticmethod
    def _draw_count(frame, count: int) -> None:
        """Draws "Products: N" in white on a solid dark panel so it stays readable on busy shelves."""
        text = f"Products: {count}"
        scale = max(0.5, min(frame.shape[:2]) / 600)
        weight = max(1, round(scale * 2))
        (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, weight)
        pad = round(8 * scale)
        cv2.rectangle(frame, (0, 0), (text_w + 2 * pad, text_h + baseline + 2 * pad), (0, 0, 0), cv2.FILLED)
        cv2.putText(
            frame,
            text,
            (pad, pad + text_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            (255, 255, 255),
            weight,
            cv2.LINE_AA,
        )
