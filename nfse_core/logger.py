"""
Módulo de logging estruturado para o nfse-cli.

Este módulo gerencia a criação e salvamento de logs estruturados em formato JSON
para operações de emissão de NFS-e, incluindo metadados do sistema e resposta da API.
"""

import json
import os
import platform
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime

from .config import Config
from .models import Prestador, Tomador, Servico
from .api_client import RespostaAPI


@dataclass
class LogEmissao:
    """
    Estrutura de log para emissão de NFS-e.
    
    Contém todas as informações relevantes sobre uma operação de emissão,
    incluindo dados de entrada, resposta da API e metadados do sistema.
    
    Attributes:
        timestamp: Timestamp da operação no formato YYYYMMDD_HHMMSS
        ambiente: Ambiente usado ('producao' ou 'producaorestrita')
        dry_run: Indica se foi uma simulação (True) ou emissão real (False)
        prestador: Dados completos do prestador (dict)
        tomador: Dados completos do tomador (dict)
        servico: Dados completos do serviço (dict)
        valor: Valor monetário do serviço
        data_emissao: Data/hora de emissão no formato ISO 8601
        id_dps: ID do DPS gerado
        resposta_api: Resposta completa da API (dict)
        metadados: Metadados do sistema (versão Python, SO, etc)
    """
    timestamp: str
    ambiente: str
    dry_run: bool
    prestador: Dict[str, Any]
    tomador: Dict[str, Any]
    servico: Dict[str, Any]
    valor: float
    data_emissao: str
    id_dps: str
    resposta_api: Dict[str, Any]
    metadados: Dict[str, Any]
    
    def para_dict(self) -> Dict[str, Any]:
        """
        Converte o log para dicionário.
        
        Returns:
            Dicionário com todos os campos do log
            
        Example:
            >>> log = LogEmissao(...)
            >>> dados = log.para_dict()
            >>> print(dados['timestamp'])
        """
        return asdict(self)
    
    def salvar(self, caminho: str):
        """
        Salva log em arquivo JSON formatado.
        
        O arquivo é salvo com indentação de 2 espaços para facilitar leitura humana.
        Cria o diretório automaticamente se não existir.
        
        Args:
            caminho: Caminho onde salvar o arquivo JSON
            
        Raises:
            IOError: Se houver erro ao salvar o arquivo
            
        Example:
            >>> log = LogEmissao(...)
            >>> log.salvar('logs/20240115_143022_12345678000190_98765432000100.json')
        """
        # Criar diretório se não existir
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        try:
            # Converter para dict
            dados = self.para_dict()
            
            # Salvar com formatação (pretty-printed)
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Erro ao salvar log em {caminho}: {e}")


def criar_log_emissao(
    config: Config,
    prestador: Prestador,
    tomador: Tomador,
    servico: Servico,
    valor: float,
    data_emissao: str,
    id_dps: str,
    resposta: RespostaAPI,
    timestamp: str
) -> LogEmissao:
    """
    Cria objeto LogEmissao a partir dos dados da operação.
    
    Inclui resposta completa da API e indicador de dry_run se aplicável.
    Converte os objetos de modelo (Prestador, Tomador, Servico) para dicionários.
    
    Args:
        config: Configuração da aplicação
        prestador: Dados do prestador
        tomador: Dados do tomador
        servico: Dados do serviço
        valor: Valor monetário do serviço
        data_emissao: Data/hora de emissão no formato ISO 8601
        id_dps: ID do DPS gerado
        resposta: Resposta da API
        timestamp: Timestamp da operação no formato YYYYMMDD_HHMMSS
        
    Returns:
        Instância de LogEmissao com todos os dados
        
    Example:
        >>> config = Config.carregar()
        >>> prestador = Prestador.carregar('prestadores/prestador.json')
        >>> tomador = Tomador.carregar('tomadores/tomador.json')
        >>> servico = Servico.carregar('servicos/servico.json')
        >>> resposta = RespostaAPI(sucesso=True, status_code=201, dados={...})
        >>> log = criar_log_emissao(
        ...     config, prestador, tomador, servico,
        ...     1500.00, '2024-01-15T14:30:22-03:00',
        ...     'ID_DPS', resposta, '20240115_143022'
        ... )
    """
    # Converter modelos para dicionários
    prestador_dict = asdict(prestador)
    tomador_dict = asdict(tomador)
    servico_dict = asdict(servico)
    
    # Construir dicionário de resposta da API
    resposta_dict = {
        'sucesso': resposta.sucesso,
        'status_code': resposta.status_code,
        'dados': resposta.dados,
        'erro': resposta.erro
    }
    
    # Se foi dry_run, adicionar indicador explícito
    if config.dry_run:
        resposta_dict['dry_run'] = True
    
    # Obter metadados do sistema
    metadados = obter_metadados()
    
    # Criar e retornar log
    return LogEmissao(
        timestamp=timestamp,
        ambiente=config.ambiente,
        dry_run=config.dry_run,
        prestador=prestador_dict,
        tomador=tomador_dict,
        servico=servico_dict,
        valor=valor,
        data_emissao=data_emissao,
        id_dps=id_dps,
        resposta_api=resposta_dict,
        metadados=metadados
    )


def obter_metadados() -> Dict[str, str]:
    """
    Obtém metadados do sistema.
    
    Coleta informações sobre:
    - Versão do Python
    - Sistema operacional
    - Versão do nfse-cli
    
    Returns:
        Dicionário com metadados do sistema
        
    Example:
        >>> metadados = obter_metadados()
        >>> print(metadados['versao_python'])
        '3.9.7'
        >>> print(metadados['sistema_operacional'])
        'Linux'
    """
    # Versão do Python
    versao_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Sistema operacional
    sistema_operacional = platform.system()
    
    # Versão do nfse-cli (pode ser obtida de um arquivo de versão ou hardcoded)
    # Por enquanto, usamos uma versão fixa
    versao_nfse_cli = "2.0.0"
    
    return {
        'versao_python': versao_python,
        'sistema_operacional': sistema_operacional,
        'versao_nfse_cli': versao_nfse_cli
    }
