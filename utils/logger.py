import logging
import os

def setup_logging(log_dir="logs", log_file="sender.log"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/{log_file}", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
