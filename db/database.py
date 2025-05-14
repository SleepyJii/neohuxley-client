
from typing import Dict, List, Optional
from pathlib import Path

import uuid
import json

from utils.config import APP_ROOT

DB_ROOT = Path(APP_ROOT) / 'db'


class Database:

    @staticmethod
    def get_users() -> List[str]:
        pass

    def check_user(user: str) -> bool:
        pass

    @staticmethod
    def store(json_obj, user: str, table: str, _uuid: Optional[str] = None):

        table_dir = DB_ROOT / table
        if not table_dir.exists():
            raise Exception(f'unknown table `{table}`')

        user_dir = table_dir / user
        if not user_dir.exists():
            raise Exception(f'`{user}` is not a valid user')
        
        if _uuid is None:
            _uuid = uuid.uuid4()
        with open(str(user_dir / f'{_uuid}.json'), 'w') as f:
            json.dump(json_obj, f)



