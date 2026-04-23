from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.services.nebula_service import NebulaService
from config import settings, get_business_space


def build() -> None:
    space_name = get_business_space("genshin")
    logger.info("Ensuring Nebula space exists: %s", space_name)
    svc = NebulaService(
        host=settings.nebula_host,
        port=settings.nebula_port,
        username=settings.nebula_username,
        password=settings.nebula_password,
        space=space_name,
    )
    svc.connect(use_space=False)
    try:
        svc.create_space(space_name=space_name, partition_num=5, replica_factor=1, vid_type="FIXED_STRING(128)")
        svc.select_space(space_name)
        svc.create_tag("Character", {"photo": "string", "name_zh": "string", "name_en": "string"})
        svc.create_edge_type(
            "Character_to_Character",
            {
                "source_name_en": "string",
                "target_name_en": "string",
                "source_name_zh": "string",
                "target_name_zh": "string",
                "title_en": "string",
                "title_zh": "string",
            },
        )
        logger.info("Nebula schema ready for space: %s", space_name)
    finally:
        svc.close()


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        logger.exception("Failed to build Nebula schema: %s", exc)
        raise