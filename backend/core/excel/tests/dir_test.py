import pandas as pd
import pytest
from pathlib import Path
from pandas.testing import assert_frame_equal

from backend.core.excel.sales_report_v2 import get_add_data, open_file

ADD_DATA_PATH = Path('D:\Работа\Тестовые данные\Данные')


@pytest.fixture
def files_xlsx() -> list[Path]:
    path = Path(ADD_DATA_PATH)
    assert path.exists(), f"Директория не найдена: {path}"
    return list(Path(ADD_DATA_PATH).iterdir())


def test_get_add_data():
    assert isinstance(get_add_data('ВРН'), dict)


def test_open_file(files_xlsx):
    assert files_xlsx
    masks = {
        'Матрица': {},
        'Номенклатура': {'header': 1}
    }
    files = files_xlsx
    for f in files:
        if f.stem in masks:
            result = open_file(f, masks[f.stem])
            assert isinstance(result, pd.DataFrame)
