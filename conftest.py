"""
Configuração do pytest e fixtures básicas para testes do nfse-cli
"""

import warnings
import pytest
import sys
from hypothesis import settings, Verbosity
from datetime import datetime
from typing import Dict

# Configurar encoding UTF-8 para stdout/stderr no Windows
# Isso evita erros de encoding com emojis e caracteres especiais
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Suprimir warnings de deprecação do signxml relacionados a algoritmos SECT
# que serão removidos em versões futuras do cryptography.
# Isso não afeta a funcionalidade pois usamos apenas RSA-SHA1 para assinatura XML.
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except ImportError:
    pass

# Configuração global do Hypothesis para property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.load_profile("default")


# ============================================================================
# Fixtures de Configuração
# ============================================================================

@pytest.fixture
def config_exemplo() -> Dict:
    """Fixture com configuração de exemplo para testes"""
    return {
        "urls": {
            "producao": "https://adn.nfse.gov.br",
            "producaorestrita": "https://adn.producaorestrita.nfse.gov.br"
        },
        "arquivo_cert_pfx": "cert/certificado.pfx",
        "arquivo_cert_senha": "cert/certificado.secret",
        "serie": 1,
        "proximo_numero": 1,
        "versao_aplicativo": "nfse-cli-2.0.0",
        "defaults": {
            "ambiente": "producaorestrita",
            "dry_run": True,
            "timeout": 30,
            "prestador": "prestadores/prestador_12345678000190.json",
            "tomador": "tomadores/tomador_exemplo.json",
            "servicos": "servicos/servico_010101.json"
        }
    }


# ============================================================================
# Fixtures de Dados de Prestador
# ============================================================================

@pytest.fixture
def prestador_exemplo() -> Dict:
    """Fixture com dados de prestador de exemplo"""
    return {
        "CNPJ": "12345678000190",
        "xNome": "EMPRESA EXEMPLO LTDA",
        "cMun": "3550308",
        "IM": "12345678",
        "email": "contato@empresa.com.br",
        "regTrib": {
            "opSimpNac": 1,
            "regEspTrib": 0,
            "regApTribSN": None
        }
    }


@pytest.fixture
def prestador_simples_nacional() -> Dict:
    """Fixture com prestador optante do Simples Nacional"""
    return {
        "CNPJ": "98765432000100",
        "xNome": "EMPRESA SIMPLES LTDA",
        "cMun": "3550308",
        "IM": "87654321",
        "email": "contato@simples.com.br",
        "regTrib": {
            "opSimpNac": 3,
            "regEspTrib": 0,
            "regApTribSN": 1
        }
    }


# ============================================================================
# Fixtures de Dados de Tomador
# ============================================================================

@pytest.fixture
def tomador_exemplo() -> Dict:
    """Fixture com dados de tomador de exemplo"""
    return {
        "CNPJ": "98765432000100",
        "xNome": "CLIENTE EXEMPLO LTDA",
        "email": "financeiro@cliente.com.br",
        "end": {
            "xLgr": "Avenida Paulista",
            "nro": "1000",
            "xBairro": "Bela Vista",
            "cMun": "3550308",
            "CEP": "01310100"
        }
    }


@pytest.fixture
def tomador_cpf() -> Dict:
    """Fixture com tomador pessoa física (CPF)"""
    return {
        "CPF": "12345678901",
        "xNome": "JOAO DA SILVA",
        "email": "joao@email.com",
        "end": {
            "xLgr": "Rua das Flores",
            "nro": "123",
            "xBairro": "Centro",
            "cMun": "3550308",
            "CEP": "01234567"
        }
    }


# ============================================================================
# Fixtures de Dados de Serviço
# ============================================================================

@pytest.fixture
def servico_exemplo() -> Dict:
    """Fixture com dados de serviço de exemplo"""
    return {
        "xDescServ": "SERVICOS DE CONSULTORIA EM TECNOLOGIA DA INFORMACAO",
        "cTribNac": "010101",
        "cLocPrestacao": "3550308",
        "cTribMun": "001",
        "cNBS": None,
        "cIntContrib": None
    }


@pytest.fixture
def servico_local_prestacao() -> Dict:
    """Fixture com serviço que incide no local da prestação"""
    return {
        "xDescServ": "SERVICOS DE CONSTRUCAO CIVIL",
        "cTribNac": "070201",
        "cLocPrestacao": "3550308",
        "cTribMun": "002",
        "cNBS": None,
        "cIntContrib": None
    }


# ============================================================================
# Fixtures de Valores e Datas
# ============================================================================

@pytest.fixture
def valor_exemplo() -> float:
    """Fixture com valor de exemplo para serviço"""
    return 1500.00


@pytest.fixture
def data_emissao_exemplo() -> str:
    """Fixture com data de emissão de exemplo no formato ISO 8601"""
    return "2024-01-15T14:30:22-03:00"


@pytest.fixture
def timestamp_exemplo() -> str:
    """Fixture com timestamp de exemplo no formato YYYYMMDD_HHMMSS"""
    return "20240115_143022"


# ============================================================================
# Fixtures de Arquivos Temporários
# ============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture que fornece um diretório temporário para testes"""
    return tmp_path


@pytest.fixture
def temp_json_file(tmp_path):
    """Fixture que cria um arquivo JSON temporário"""
    def _create_json(data: Dict, filename: str = "test.json"):
        import json
        file_path = tmp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path
    return _create_json


# ============================================================================
# Fixtures de Mock de API
# ============================================================================

@pytest.fixture
def mock_api_response_sucesso() -> Dict:
    """Fixture com resposta de sucesso da API"""
    return {
        "tipoAmbiente": 2,
        "versaoAplicativo": "1.0.0",
        "dataHoraProcessamento": "2024-01-15T14:30:25-03:00",
        "chaveAcesso": "35503082123456780001900001000000000000001",
        "nfseXmlGZipB64": "H4sIAAAAAAAA..."
    }


@pytest.fixture
def mock_api_response_erro() -> Dict:
    """Fixture com resposta de erro da API"""
    return {
        "codigo": "E1001",
        "mensagem": "Dados inválidos",
        "detalhes": "O código de município '123' não é válido. Deve ter 7 dígitos."
    }


# ============================================================================
# Markers de Teste
# ============================================================================

def pytest_configure(config):
    """Configura markers customizados para pytest"""
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "property: marca testes property-based"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
