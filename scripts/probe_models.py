import sys, logging
logging.disable(logging.WARNING)
from inference import get_model
from src import config
for mid in sys.argv[1:]:
    try:
        m = get_model(model_id=mid, api_key=config.ROBOFLOW_API_KEY)
        print("OK  ", mid, getattr(m, "class_names", None), flush=True)
    except Exception as e:
        print("FAIL", mid, type(e).__name__, str(e)[:120].replace("\n"," "), flush=True)
