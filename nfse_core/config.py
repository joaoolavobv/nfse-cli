"""
Módulo de gerenciamento de configuração do nfse-cli.

Este módulo gerencia a leitura e escrita do arquivo de configuração config.json,
incluindo URLs da API, configurações de ambiente, certificados e valores padrão.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional


@dataclass
class Config:
    """
    Configuração da aplicação nfse-cli.
    
    Attributes:
        ambiente: Ambiente de execução ('producao' ou 'producaorestrita')
        dry_run: Modo de simulação (não envia para API se True)
        timeout: Timeout em segundos para requisições HTTP (padrão: 30)
        urls: Dicionário com URLs da API por ambiente
        arquivo_cert_pfx: Caminho para o arquivo de certificado PFX
        arquivo_cert_senha: Caminho para o arquivo com a senha do certificado
        serie: Série do DPS
        proximo_numero: Próximo número de DPS a ser usado
        versao_aplicativo: Versão do aplicativo para incluir no XML
        defaults: Dicionário com caminhos padrão para prestador, tomador e serviços
    """
    ambiente: str = "producaorestrita"
    dry_run: bool = True
    timeout: int = 30
    urls: Dict[str, str] = field(default_factory=lambda: {
        "producao": "https://adn.nfse.gov.br",
        "producaorestrita": "https://adn.producaorestrita.nfse.gov.br"
    })
    arquivo_cert_pfx: str = "cert/certificado.pfx"
    arquivo_cert_senha: str = "cert/certificado.secret"
    serie: int = 1
    proximo_numero: int = 1
    versao_aplicativo: str = "nfse-cli-2.0.0"
    defaults: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def carregar(cls, caminho: str = 'config.json') -> 'Config':
        """
        Carrega configuração do arquivo JSON.
        
        Se o arquivo não existir, retorna uma instância com valores padrão.
        
        Args:
            caminho: Caminho para o arquivo de configuração (padrão: 'config.json')
            
        Returns:
            Instância de Config com os dados carregados ou valores padrão
            
        Example:
            >>> config = Config.carregar()
            >>> config = Config.carregar('custom_config.json')
        """
        if not os.path.exists(caminho):
            # Retorna configuração com valores padrão se arquivo não existir
            return cls()
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Criar instância com valores do arquivo
            # Usar valores padrão para campos não presentes no arquivo
            defaults = dados.get('defaults', {})
            
            return cls(
                ambiente=defaults.get('ambiente', 'producaorestrita'),
                dry_run=defaults.get('dry_run', True),
                timeout=defaults.get('timeout', 30),
                urls=dados.get('urls', {
                    "producao": "https://adn.nfse.gov.br",
                    "producaorestrita": "https://adn.producaorestrita.nfse.gov.br"
                }),
                arquivo_cert_pfx=dados.get('arquivo_cert_pfx', 'cert/certificado.pfx'),
                arquivo_cert_senha=dados.get('arquivo_cert_senha', 'cert/certificado.secret'),
                serie=dados.get('serie', 1),
                proximo_numero=dados.get('proximo_numero', 1),
                versao_aplicativo=dados.get('versao_aplicativo', 'nfse-cli-2.0.0'),
                defaults=defaults
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao ler arquivo de configuração {caminho}: {e}")
        except Exception as e:
            raise IOError(f"Erro ao carregar configuração de {caminho}: {e}")

    def salvar(self, caminho: str = 'config.json'):
        """
        Salva configuração no arquivo JSON formatado.
        
        O arquivo é salvo com indentação de 2 espaços para facilitar leitura.
        
        Args:
            caminho: Caminho para o arquivo de configuração (padrão: 'config.json')
            
        Raises:
            IOError: Se houver erro ao salvar o arquivo
            
        Example:
            >>> config = Config()
            >>> config.salvar()
            >>> config.salvar('custom_config.json')
        """
        try:
            # Converter dataclass para dicionário
            dados = asdict(self)
            
            # Salvar com formatação
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Erro ao salvar configuração em {caminho}: {e}")

    def atualizar_default(self, tipo: str, caminho: str):
        """
        Atualiza um caminho padrão no dicionário defaults.
        
        Args:
            tipo: Tipo de default a atualizar ('prestador' ou 'servicos')
            caminho: Caminho do arquivo a definir como padrão
            
        Raises:
            ValueError: Se o tipo não for 'prestador' ou 'servicos'
            
        Example:
            >>> config = Config()
            >>> config.atualizar_default('prestador', 'prestadores/prestador_12345678000190.json')
            >>> config.atualizar_default('servicos', 'servicos/servico_010101.json')
        """
        tipos_validos = ['prestador', 'servicos']
        if tipo not in tipos_validos:
            raise ValueError(f"Tipo '{tipo}' inválido. Deve ser um de: {', '.join(tipos_validos)}")
        
        self.defaults[tipo] = caminho

    def obter_url_api(self, ambiente: Optional[str] = None) -> str:
        """
        Retorna URL da API para o ambiente especificado.
        
        Se ambiente não for fornecido, usa o ambiente configurado na instância.
        Suporta override via parâmetro para permitir mudança temporária de ambiente.
        
        Args:
            ambiente: Ambiente desejado ('producao' ou 'producaorestrita').
                     Se None, usa self.ambiente
                     
        Returns:
            URL base da API para o ambiente especificado
            
        Raises:
            ValueError: Se o ambiente não for válido
            
        Example:
            >>> config = Config(ambiente='producaorestrita')
            >>> config.obter_url_api()
            'https://adn.producaorestrita.nfse.gov.br'
            >>> config.obter_url_api('producao')
            'https://adn.nfse.gov.br'
        """
        # Usar ambiente fornecido ou o configurado na instância
        env = ambiente if ambiente is not None else self.ambiente
        
        # Validar ambiente
        if env not in self.urls:
            ambientes_validos = ', '.join(self.urls.keys())
            raise ValueError(
                f"Ambiente '{env}' inválido. Ambientes válidos: {ambientes_validos}"
            )
        
        return self.urls[env]
