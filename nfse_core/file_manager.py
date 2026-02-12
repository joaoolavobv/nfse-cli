"""
Módulo de gerenciamento de arquivos e diretórios.

Este módulo é responsável por:
- Criar estrutura de diretórios necessária
- Gerar nomes padronizados de arquivos
- Salvar arquivos (DPS, NFS-e, DANFSe, logs)
"""

import os
import json
from datetime import datetime
from typing import Dict, Any


class FileManager:
    """Gerenciador de arquivos e diretórios do sistema"""
    
    # Lista de diretórios necessários para o funcionamento do sistema
    DIRETORIOS = [
        'cert',
        'logs',
        'prestadores',
        'tomadores',
        'servicos',
        'danfse',
        'nfse',
        'dps'
    ]
    
    @staticmethod
    def criar_diretorios(silent: bool = False):
        """
        Cria todos os diretórios necessários se não existirem.
        
        Args:
            silent: Se True, não exibe mensagens informativas
        """
        for diretorio in FileManager.DIRETORIOS:
            if not os.path.exists(diretorio):
                os.makedirs(diretorio, exist_ok=True)
                if not silent:
                    print(f"✓ Diretório criado: {diretorio}/")
            else:
                if not silent:
                    print(f"✓ Diretório já existe: {diretorio}/")
    
    @staticmethod
    def gerar_timestamp() -> str:
        """
        Gera timestamp no formato YYYYMMDD_HHMMSS.
        
        Returns:
            String com timestamp formatado (ex: "20240115_143022")
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def gerar_nome_arquivo(
        timestamp: str,
        cnpj_prestador: str,
        documento_tomador: str,
        extensao: str
    ) -> str:
        """
        Gera nome padronizado de arquivo.
        
        Formato: {timestamp}_{cnpj_prestador}_{documento_tomador}.{extensao}
        
        Args:
            timestamp: Timestamp no formato YYYYMMDD_HHMMSS
            cnpj_prestador: CNPJ do prestador (14 dígitos)
            documento_tomador: CPF ou CNPJ do tomador
            extensao: Extensão do arquivo (sem ponto)
        
        Returns:
            Nome do arquivo formatado
        """
        nome_base = f"{timestamp}_{cnpj_prestador}_{documento_tomador}"
        if extensao:
            return f"{nome_base}.{extensao}"
        return nome_base
    
    @staticmethod
    def salvar_dps(xml: str, nome_arquivo: str, silent: bool = False):
        """
        Salva XML do DPS no diretório dps/.
        
        Args:
            xml: Conteúdo XML do DPS
            nome_arquivo: Nome do arquivo (com extensão)
            silent: Se True, não exibe mensagens informativas
        """
        diretorio = 'dps'
        if not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(xml)
        
        if not silent:
            print(f"✓ DPS salvo: {caminho_completo}")
    
    @staticmethod
    def salvar_nfse(xml: str, nome_arquivo: str, silent: bool = False):
        """
        Salva XML da NFS-e no diretório nfse/.
        
        Args:
            xml: Conteúdo XML da NFS-e
            nome_arquivo: Nome do arquivo (com extensão)
            silent: Se True, não exibe mensagens informativas
        """
        diretorio = 'nfse'
        if not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(xml)
        
        if not silent:
            print(f"✓ NFS-e salva: {caminho_completo}")
    
    @staticmethod
    def salvar_danfse(pdf_bytes: bytes, nome_arquivo: str, silent: bool = False):
        """
        Salva PDF do DANFSe no diretório danfse/.
        
        Args:
            pdf_bytes: Conteúdo binário do PDF
            nome_arquivo: Nome do arquivo (com extensão)
            silent: Se True, não exibe mensagens informativas
        """
        diretorio = 'danfse'
        if not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        with open(caminho_completo, 'wb') as f:
            f.write(pdf_bytes)
        
        if not silent:
            print(f"✓ DANFSe salvo: {caminho_completo}")
    
    @staticmethod
    def salvar_log(dados: Dict[str, Any], nome_arquivo: str, silent: bool = False):
        """
        Salva log JSON no diretório logs/.
        
        Args:
            dados: Dicionário com dados do log
            nome_arquivo: Nome do arquivo (com extensão)
            silent: Se True, não exibe mensagens informativas
        """
        diretorio = 'logs'
        if not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        if not silent:
            print(f"✓ Log salvo: {caminho_completo}")
