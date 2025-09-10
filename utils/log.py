from typing import Optional

import logging

def setup(message: str) -> Optional[str]:
    logging.basicConfig(
        filename='tilf.log',
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    return logging.info(message)