import pytest
import json
import os
from pathlib import Path
from typing import Dict, List
import tempfile
import shutil
from unittest.mock import patch

@pytest.fixture(scope="session")
def test_data() -> Dict:
    """
    Fixture que carga los datos de prueba desde el archivo JSON.
    """
    data_file = Path(__file__).parent.parent / "data" / "sample_licitaciones.json"
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def test_licitaciones(test_data) -> List[Dict]:
    """
    Fixture que proporciona la lista de licitaciones de prueba.
    """
    return test_data["licitaciones"]

@pytest.fixture(scope="function")
def temp_dir():
    """
    Fixture que proporciona un directorio temporal para los tests.
    Se crea nuevo para cada test.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    try:
        shutil.rmtree(temp_dir)
    except (OSError, IOError) as e:
        print(f"Error limpiando directorio temporal: {e}")

@pytest.fixture(scope="session")
def test_env():
    """
    Fixture que configura variables de entorno para testing.
    """
    original_env = dict(os.environ)
    
    # Configurar variables para testing
    os.environ.update({
        "OPENAI_API_KEY": "test-key-123",
        "DEBUG": "True",
        "PORT": "5000",
        "LOG_LEVEL": "INFO"
    })
    
    yield
    
    # Restaurar variables originales
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(scope="function")
def mock_openai():
    """
    Fixture que proporciona un mock para las llamadas a OpenAI.
    """
    mock = MagicMock()
    mock.create.return_value = {
        "choices": [{
            "message": {
                "content": "Respuesta de prueba de OpenAI"
            }
        }]
    }
    
    with patch("langchain_openai.ChatOpenAI", return_value=mock):
        yield mock 