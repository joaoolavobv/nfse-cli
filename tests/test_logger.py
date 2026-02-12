"""
Testes para o módulo de logging (logger.py).

Testa a criação de logs estruturados, salvamento em JSON e obtenção de metadados.
"""

import json
import os
import tempfile
import pytest
from datetime import datetime

from nfse_core.logger import LogEmissao, criar_log_emissao, obter_metadados
from nfse_core.config import Config
from nfse_core.models import Prestador, Tomador, Servico, RegimeTributario, Endereco
from nfse_core.api_client import RespostaAPI


def test_log_emissao_para_dict():
    """Testa conversão de LogEmissao para dicionário"""
    log = LogEmissao(
        timestamp="20240115_143022",
        ambiente="producaorestrita",
        dry_run=True,
        prestador={"CNPJ": "12345678000190", "xNome": "EMPRESA TESTE"},
        tomador={"CNPJ": "98765432000100", "xNome": "CLIENTE TESTE"},
        servico={"xDescServ": "SERVICO TESTE", "cTribNac": "010101"},
        valor=1500.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS_TESTE",
        resposta_api={"sucesso": True, "status_code": 201},
        metadados={"versao_python": "3.9.7"}
    )
    
    dados = log.para_dict()
    
    assert isinstance(dados, dict)
    assert dados['timestamp'] == "20240115_143022"
    assert dados['ambiente'] == "producaorestrita"
    assert dados['dry_run'] is True
    assert dados['valor'] == 1500.00


def test_log_emissao_salvar(tmp_path):
    """Testa salvamento de log em arquivo JSON"""
    log = LogEmissao(
        timestamp="20240115_143022",
        ambiente="producaorestrita",
        dry_run=True,
        prestador={"CNPJ": "12345678000190"},
        tomador={"CNPJ": "98765432000100"},
        servico={"xDescServ": "SERVICO TESTE"},
        valor=1500.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS_TESTE",
        resposta_api={"sucesso": True},
        metadados={"versao_python": "3.9.7"}
    )
    
    # Salvar em diretório temporário
    caminho = tmp_path / "logs" / "teste.json"
    log.salvar(str(caminho))
    
    # Verificar que arquivo foi criado
    assert caminho.exists()
    
    # Verificar conteúdo do arquivo
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    assert dados['timestamp'] == "20240115_143022"
    assert dados['ambiente'] == "producaorestrita"
    assert dados['dry_run'] is True
    assert dados['valor'] == 1500.00


def test_obter_metadados():
    """Testa obtenção de metadados do sistema"""
    metadados = obter_metadados()
    
    assert isinstance(metadados, dict)
    assert 'versao_python' in metadados
    assert 'sistema_operacional' in metadados
    assert 'versao_nfse_cli' in metadados
    
    # Verificar que versão do Python tem formato correto
    versao_python = metadados['versao_python']
    partes = versao_python.split('.')
    assert len(partes) == 3
    assert all(parte.isdigit() for parte in partes)
    
    # Verificar que sistema operacional não está vazio
    assert len(metadados['sistema_operacional']) > 0
    
    # Verificar que versão do nfse-cli está presente
    assert metadados['versao_nfse_cli'] == "2.0.0"


def test_criar_log_emissao():
    """Testa criação de log completo a partir dos dados da operação"""
    # Criar objetos de teste
    config = Config(
        ambiente="producaorestrita",
        dry_run=True
    )
    
    prestador = Prestador(
        CNPJ="12345678000190",
        xNome="EMPRESA TESTE LTDA",
        cMun="3550308",
        regTrib=RegimeTributario(opSimpNac=1, regEspTrib=0)
    )
    
    tomador = Tomador(
        CNPJ="98765432000100",
        xNome="CLIENTE TESTE LTDA",
        end=Endereco(
            xLgr="Avenida Teste",
            nro="100",
            xBairro="Centro",
            cMun="3550308",
            CEP="01310100"
        )
    )
    
    servico = Servico(
        xDescServ="SERVICOS DE TESTE",
        cTribNac="010101",
        cLocPrestacao="3550308"
    )
    
    resposta = RespostaAPI(
        sucesso=True,
        status_code=201,
        dados={
            "chaveAcesso": "12345678901234567890123456789012345678901234567890",
            "tipoAmbiente": 2
        }
    )
    
    # Criar log
    log = criar_log_emissao(
        config=config,
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        valor=1500.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS_TESTE",
        resposta=resposta,
        timestamp="20240115_143022"
    )
    
    # Verificar campos do log
    assert log.timestamp == "20240115_143022"
    assert log.ambiente == "producaorestrita"
    assert log.dry_run is True
    assert log.valor == 1500.00
    assert log.data_emissao == "2024-01-15T14:30:22-03:00"
    assert log.id_dps == "ID_DPS_TESTE"
    
    # Verificar que prestador foi convertido para dict
    assert isinstance(log.prestador, dict)
    assert log.prestador['CNPJ'] == "12345678000190"
    assert log.prestador['xNome'] == "EMPRESA TESTE LTDA"
    
    # Verificar que tomador foi convertido para dict
    assert isinstance(log.tomador, dict)
    assert log.tomador['CNPJ'] == "98765432000100"
    
    # Verificar que serviço foi convertido para dict
    assert isinstance(log.servico, dict)
    assert log.servico['xDescServ'] == "SERVICOS DE TESTE"
    
    # Verificar resposta da API
    assert log.resposta_api['sucesso'] is True
    assert log.resposta_api['status_code'] == 201
    assert log.resposta_api['dry_run'] is True  # Deve incluir indicador de dry_run
    
    # Verificar metadados
    assert isinstance(log.metadados, dict)
    assert 'versao_python' in log.metadados
    assert 'sistema_operacional' in log.metadados


def test_criar_log_emissao_sem_dry_run():
    """Testa criação de log em modo de emissão real (não dry-run)"""
    config = Config(
        ambiente="producao",
        dry_run=False
    )
    
    prestador = Prestador(
        CNPJ="12345678000190",
        xNome="EMPRESA TESTE",
        cMun="3550308",
        regTrib=RegimeTributario(opSimpNac=1, regEspTrib=0)
    )
    
    tomador = Tomador(
        CNPJ="98765432000100",
        xNome="CLIENTE TESTE"
    )
    
    servico = Servico(
        xDescServ="SERVICO TESTE",
        cTribNac="010101",
        cLocPrestacao="3550308"
    )
    
    resposta = RespostaAPI(
        sucesso=True,
        status_code=201,
        dados={"chaveAcesso": "12345"}
    )
    
    log = criar_log_emissao(
        config=config,
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        valor=2000.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS",
        resposta=resposta,
        timestamp="20240115_143022"
    )
    
    # Verificar que dry_run é False
    assert log.dry_run is False
    assert log.ambiente == "producao"
    
    # Verificar que resposta NÃO tem indicador dry_run quando é False
    assert 'dry_run' not in log.resposta_api or log.resposta_api.get('dry_run') is False


def test_log_emissao_com_erro_api():
    """Testa criação de log quando há erro na API"""
    config = Config(ambiente="producaorestrita", dry_run=False)
    
    prestador = Prestador(
        CNPJ="12345678000190",
        xNome="EMPRESA TESTE",
        cMun="3550308",
        regTrib=RegimeTributario(opSimpNac=1, regEspTrib=0)
    )
    
    tomador = Tomador(CNPJ="98765432000100", xNome="CLIENTE TESTE")
    servico = Servico(xDescServ="SERVICO", cTribNac="010101", cLocPrestacao="3550308")
    
    # Resposta com erro
    resposta = RespostaAPI(
        sucesso=False,
        status_code=400,
        dados={},
        erro="Erro de validação: Campo obrigatório ausente"
    )
    
    log = criar_log_emissao(
        config=config,
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        valor=1000.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS",
        resposta=resposta,
        timestamp="20240115_143022"
    )
    
    # Verificar que erro foi incluído no log
    assert log.resposta_api['sucesso'] is False
    assert log.resposta_api['status_code'] == 400
    assert log.resposta_api['erro'] == "Erro de validação: Campo obrigatório ausente"


def test_log_salvar_cria_diretorio_automaticamente(tmp_path):
    """Testa que salvar() cria diretório automaticamente se não existir"""
    log = LogEmissao(
        timestamp="20240115_143022",
        ambiente="producaorestrita",
        dry_run=True,
        prestador={},
        tomador={},
        servico={},
        valor=1000.00,
        data_emissao="2024-01-15T14:30:22-03:00",
        id_dps="ID_DPS",
        resposta_api={},
        metadados={}
    )
    
    # Caminho com diretórios que não existem
    caminho = tmp_path / "logs" / "subdir" / "teste.json"
    
    # Verificar que diretório não existe
    assert not caminho.parent.exists()
    
    # Salvar log
    log.salvar(str(caminho))
    
    # Verificar que diretório foi criado
    assert caminho.parent.exists()
    assert caminho.exists()
