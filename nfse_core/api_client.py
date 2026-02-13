"""
Módulo de cliente da API da NFS-e.

Este módulo gerencia a comunicação com a API oficial da Sefin Nacional,
incluindo emissão de NFS-e, consultas e download de DANFSe.
"""

import os
import tempfile
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from .config import Config


def _obter_mensagem_erro_http(status_code: int, operacao: str = "geral") -> str:
    """
    Retorna mensagem de erro descritiva baseada no código HTTP e operação.
    
    Args:
        status_code: Código de status HTTP
        operacao: Tipo de operação ("emissao", "consulta", "download", "geral")
    
    Returns:
        Mensagem de erro descritiva
    """
    if operacao == "emissao":
        mensagens = {
            400: "Requisição inválida. Verifique os dados do DPS.",
            401: "Não autorizado. Verifique se o certificado digital é válido.",
            403: "Acesso negado. Verifique as permissões do certificado.",
            404: "Endpoint não encontrado. Verifique se o ambiente está correto e se a API está disponível.",
            422: "Dados inválidos. Verifique os campos do DPS.",
            502: "Servidor indisponível (Bad Gateway). O servidor do governo pode estar temporariamente fora do ar.",
            503: "Serviço indisponível. Tente novamente em alguns minutos.",
        }
    elif operacao == "consulta":
        mensagens = {
            400: "Requisição inválida. Verifique a chave de acesso.",
            401: "Não autorizado. Verifique se o certificado digital é válido.",
            403: "Acesso negado. Verifique as permissões do certificado.",
            404: "NFS-e não encontrada. Verifique se a chave de acesso está correta e se a nota existe no ambiente selecionado.",
            502: "Servidor indisponível (Bad Gateway). O servidor do governo pode estar temporariamente fora do ar.",
            503: "Serviço indisponível. Tente novamente em alguns minutos.",
        }
    elif operacao == "download":
        mensagens = {
            400: "Requisição inválida. Verifique a chave de acesso.",
            401: "Não autorizado. Verifique se o certificado digital é válido.",
            403: "Acesso negado. Verifique as permissões do certificado.",
            404: "DANFSe não encontrado. Verifique se a chave de acesso está correta e se a nota existe no ambiente selecionado.",
            502: "Servidor indisponível (Bad Gateway). O servidor do governo pode estar temporariamente fora do ar.",
            503: "Serviço indisponível. Tente novamente em alguns minutos.",
        }
    else:
        mensagens = {
            400: "Requisição inválida.",
            401: "Não autorizado.",
            403: "Acesso negado.",
            404: "Recurso não encontrado.",
            502: "Servidor indisponível (Bad Gateway).",
            503: "Serviço indisponível.",
        }
    
    return mensagens.get(status_code, f"Servidor retornou status {status_code} sem mensagem de erro.")


@dataclass
class RespostaAPI:
    """
    Resposta da API da NFS-e.
    
    Attributes:
        sucesso: Indica se a operação foi bem-sucedida
        status_code: Código de status HTTP da resposta
        dados: Dicionário com os dados retornados pela API
        erro: Mensagem de erro, se houver
    """
    sucesso: bool
    status_code: int
    dados: Dict
    erro: Optional[str] = None




class APIClient:
    """
    Cliente para comunicação com a API da NFS-e.
    
    Gerencia autenticação mTLS com certificado digital e requisições HTTP.
    Implementa context manager para gerenciar arquivo temporário de certificado.
    
    Attributes:
        config: Configuração da aplicação
        pem_data: Certificado e chave privada em formato PEM
        temp_cert_file: Arquivo temporário do certificado (criado no __enter__)
    """
    
    def __init__(self, config: Config, pem_data: bytes):
        """
        Inicializa o cliente da API.
        
        Args:
            config: Instância de Config com configurações da aplicação
            pem_data: Certificado e chave privada em formato PEM (bytes)
        """
        self.config = config
        self.pem_data = pem_data
        self.temp_cert_file = None
    
    def __enter__(self):
        """
        Context manager: cria arquivo temporário de certificado.
        
        O arquivo temporário é necessário porque a biblioteca requests
        requer um caminho de arquivo para autenticação mTLS.
        
        Returns:
            self: Instância do APIClient
        """
        # Criar arquivo temporário para o certificado PEM
        self.temp_cert_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.pem',
            delete=False
        )
        self.temp_cert_file.write(self.pem_data)
        self.temp_cert_file.close()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager: limpa arquivo temporário de certificado.
        
        Args:
            exc_type: Tipo de exceção (se houver)
            exc_val: Valor da exceção (se houver)
            exc_tb: Traceback da exceção (se houver)
        """
        # Limpar arquivo temporário
        if self.temp_cert_file and os.path.exists(self.temp_cert_file.name):
            os.remove(self.temp_cert_file.name)

    
    def emitir_nfse(self, dps_comprimido: str, dry_run: bool = False) -> RespostaAPI:
        """
        Envia DPS para emissão de NFS-e.
        
        Se dry_run=True, simula envio sem fazer requisição real.
        
        Endpoint: POST /nfse
        Formato do payload JSON:
        {
            "dps": "<XML_GZIP_BASE64>"
        }
        
        Headers:
        - Content-Type: application/json
        - Autenticação via mTLS (certificado digital)
        
        Resposta de sucesso (201):
        {
            "tipoAmbiente": 2,
            "versaoAplicativo": "1.0.0",
            "dataHoraProcessamento": "2024-01-15T14:30:25-03:00",
            "chaveAcesso": "35503082123456780001900001000000000000001",
            "nfseXmlGZipB64": "<XML_NFSE_GZIP_BASE64>"
        }
        
        Args:
            dps_comprimido: DPS comprimido em formato Base64+Gzip
            dry_run: Se True, simula envio sem fazer requisição real
            
        Returns:
            RespostaAPI com resultado da operação
        """
        # Modo dry-run: simular envio sem fazer requisição real
        if dry_run:
            return RespostaAPI(
                sucesso=True,
                status_code=201,
                dados={
                    "tipoAmbiente": 2 if self.config.ambiente == "producaorestrita" else 1,
                    "versaoAplicativo": "simulado",
                    "dataHoraProcessamento": "2024-01-01T00:00:00-03:00",
                    "chaveAcesso": "00000000000000000000000000000000000000000000000000",
                    "nfseXmlGZipB64": "",
                    "dry_run": True
                },
                erro=None
            )
        
        # Construir URL do endpoint
        url_base = self.config.obter_url_api()
        url = f"{url_base}/nfse"
        
        # Construir payload JSON
        payload = {
            "dpsXmlGZipB64": dps_comprimido
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            # Fazer requisição POST com autenticação mTLS
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                cert=self.temp_cert_file.name,
                timeout=self.config.timeout
            )
            
            # Processar resposta
            if response.status_code in [200, 201]:
                # Sucesso
                return RespostaAPI(
                    sucesso=True,
                    status_code=response.status_code,
                    dados=response.json(),
                    erro=None
                )
            else:
                # Erro da API (emissão)
                try:
                    dados_erro = response.json()
                    mensagem_erro = dados_erro.get('mensagem', response.text)
                except:
                    mensagem_erro = response.text
                
                # Se mensagem está vazia, criar mensagem mais descritiva
                if not mensagem_erro or mensagem_erro.strip() == '':
                    mensagem_erro = _obter_mensagem_erro_http(response.status_code, 'emissao')
                return RespostaAPI(
                    sucesso=False,
                    status_code=response.status_code,
                    dados={},
                    erro=f"Erro HTTP {response.status_code}: {mensagem_erro}"
                )
        
        except requests.exceptions.Timeout:
            # Timeout na requisição
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Timeout: A API não respondeu dentro do tempo limite ({self.config.timeout} segundos)"
            )
        
        except requests.exceptions.ConnectionError as e:
            # Erro de conexão
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro de conexão: Não foi possível conectar à API. Verifique sua conexão de rede. Detalhes: {str(e)}"
            )
        
        except requests.exceptions.RequestException as e:
            # Outros erros de rede
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro de rede: {str(e)}"
            )
        
        except Exception as e:
            # Erro inesperado
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro inesperado ao enviar DPS: {str(e)}"
            )

    
    def consultar_nfse(self, chave_acesso: str) -> RespostaAPI:
        """
        Consulta NFS-e pela chave de acesso.
        
        Endpoint: GET /nfse/{chaveAcesso}
        
        Resposta de sucesso (200):
        {
            "chaveAcesso": "35503082123456780001900001000000000000001",
            "nfseXmlGZipB64": "<XML_NFSE_GZIP_BASE64>",
            "dataHoraProcessamento": "2024-01-15T14:30:25-03:00"
        }
        
        Args:
            chave_acesso: Chave de acesso da NFS-e (50 dígitos)
            
        Returns:
            RespostaAPI com resultado da consulta
        """
        # Construir URL do endpoint
        url_base = self.config.obter_url_api()
        url = f"{url_base}/nfse/{chave_acesso}"
        
        # Debug: exibir URL completa se VERBOSE estiver ativo
        from .cli import VERBOSE
        if VERBOSE:
            print(f"🔍 DEBUG: URL da requisição: {url}")
            print(f"🔍 DEBUG: Chave de acesso: {chave_acesso}")
            print(f"🔍 DEBUG: Certificado: {self.temp_cert_file.name}")
        
        try:
            # Fazer requisição GET com autenticação mTLS
            response = requests.get(
                url,
                cert=self.temp_cert_file.name,
                timeout=self.config.timeout
            )
            
            # Debug: exibir detalhes da resposta
            if VERBOSE:
                print(f"🔍 DEBUG: Status code: {response.status_code}")
                print(f"🔍 DEBUG: Headers: {dict(response.headers)}")
                print(f"🔍 DEBUG: Content-Length: {response.headers.get('content-length', 'N/A')}")
                print(f"🔍 DEBUG: Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # Tentar exibir corpo da resposta
                try:
                    if len(response.text) > 0:
                        print(f"🔍 DEBUG: Response body (primeiros 1000 chars):")
                        print(f"   {response.text[:1000]}")
                    else:
                        print(f"🔍 DEBUG: Response body: (vazio)")
                except:
                    print(f"🔍 DEBUG: Response body: (não foi possível decodificar)")
            
            # Processar resposta
            if response.status_code == 200:
                # Sucesso
                return RespostaAPI(
                    sucesso=True,
                    status_code=response.status_code,
                    dados=response.json(),
                    erro=None
                )
            else:
                # Erro da API (consulta)
                try:
                    dados_erro = response.json()
                    mensagem_erro = dados_erro.get('mensagem', response.text)
                except:
                    mensagem_erro = response.text
                
                # Se mensagem está vazia, criar mensagem mais descritiva
                if not mensagem_erro or mensagem_erro.strip() == '':
                    mensagem_erro = _obter_mensagem_erro_http(response.status_code, 'consulta')
                return RespostaAPI(
                    sucesso=False,
                    status_code=response.status_code,
                    dados={},
                    erro=f"Erro HTTP {response.status_code}: {mensagem_erro}"
                )
        
        except requests.exceptions.Timeout:
            # Timeout na requisição
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Timeout: A API não respondeu dentro do tempo limite ({self.config.timeout} segundos)"
            )
        
        except requests.exceptions.ConnectionError as e:
            # Erro de conexão
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro de conexão: Não foi possível conectar à API. Verifique sua conexão de rede. Detalhes: {str(e)}"
            )
        
        except requests.exceptions.RequestException as e:
            # Outros erros de rede
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro de rede: {str(e)}"
            )
        
        except Exception as e:
            # Erro inesperado
            return RespostaAPI(
                sucesso=False,
                status_code=0,
                dados={},
                erro=f"Erro inesperado ao consultar NFS-e: {str(e)}"
            )

    
    def baixar_danfse(self, chave_acesso: str) -> bytes:
        """
        Baixa PDF do DANFSe.
        
        Endpoint: GET /danfse/{chaveAcesso}
        
        Retorna: bytes do arquivo PDF
        
        Args:
            chave_acesso: Chave de acesso da NFS-e (50 dígitos)
            
        Returns:
            bytes: Conteúdo do PDF do DANFSe
            
        Raises:
            requests.exceptions.RequestException: Se houver erro na requisição
            ValueError: Se a resposta não for um PDF válido
        """
        # Construir URL do endpoint
        url_base = self.config.obter_url_api()
        url = f"{url_base}/danfse/{chave_acesso}"
        
        # Debug: exibir URL completa se VERBOSE estiver ativo
        from .cli import VERBOSE
        if VERBOSE:
            print(f"🔍 DEBUG: URL da requisição: {url}")
            print(f"🔍 DEBUG: Chave de acesso: {chave_acesso}")
            print(f"🔍 DEBUG: Certificado: {self.temp_cert_file.name}")
        
        try:
            # Fazer requisição GET com autenticação mTLS
            response = requests.get(
                url,
                cert=self.temp_cert_file.name,
                timeout=self.config.timeout
            )
            
            # Debug: exibir detalhes da resposta
            if VERBOSE:
                print(f"🔍 DEBUG: Status code: {response.status_code}")
                print(f"🔍 DEBUG: Headers: {dict(response.headers)}")
                print(f"🔍 DEBUG: Content-Length: {response.headers.get('content-length', 'N/A')}")
                print(f"🔍 DEBUG: Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # Tentar exibir corpo da resposta
                try:
                    if len(response.text) > 0:
                        print(f"🔍 DEBUG: Response body (primeiros 1000 chars):")
                        print(f"   {response.text[:1000]}")
                    else:
                        print(f"🔍 DEBUG: Response body: (vazio)")
                except:
                    print(f"🔍 DEBUG: Response body: (não foi possível decodificar)")
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                # Verificar se o conteúdo é um PDF
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' not in content_type.lower() and not response.content.startswith(b'%PDF'):
                    raise ValueError(
                        f"Resposta não é um PDF válido. Content-Type: {content_type}"
                    )
                
                return response.content
            else:
                # Erro da API (download)
                try:
                    dados_erro = response.json()
                    mensagem_erro = dados_erro.get('mensagem', response.text)
                except:
                    mensagem_erro = response.text
                
                # Se mensagem está vazia, criar mensagem mais descritiva
                if not mensagem_erro or mensagem_erro.strip() == '':
                    mensagem_erro = _obter_mensagem_erro_http(response.status_code, 'download')
                raise requests.exceptions.RequestException(
                    f"Erro HTTP {response.status_code}: {mensagem_erro}"
                )
        
        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException(
                f"Timeout: A API não respondeu dentro do tempo limite ({self.config.timeout} segundos)"
            )
        
        except requests.exceptions.ConnectionError as e:
            raise requests.exceptions.RequestException(
                f"Erro de conexão: Não foi possível conectar à API. Verifique sua conexão de rede. Detalhes: {str(e)}"
            )
        
        except ValueError:
            # Re-raise ValueError (resposta não é PDF)
            raise
        
        except requests.exceptions.RequestException:
            # Re-raise RequestException
            raise
        
        except Exception as e:
            raise requests.exceptions.RequestException(
                f"Erro inesperado ao baixar DANFSe: {str(e)}"
            )

