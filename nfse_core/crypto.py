"""
Módulo de criptografia e operações com certificados digitais.

Este módulo gerencia:
- Carregamento e validação de certificados digitais PFX/PKCS#12
- Assinatura digital de XML com XMLDSig
- Compressão e descompressão de XML (Gzip + Base64)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import base64
import gzip
import io
import os
import tempfile

from lxml import etree
from OpenSSL import crypto
from signxml import XMLSigner, methods


@dataclass
class CertificadoInfo:
    """
    Informações extraídas de um certificado digital.
    
    Attributes:
        titular: Nome do titular do certificado
        emissor: Nome da autoridade certificadora emissora
        validade_inicio: Data/hora de início da validade
        validade_fim: Data/hora de fim da validade
        dias_para_expirar: Número de dias até a expiração
        eh_icp_brasil: Indica se o certificado é emitido pela ICP-Brasil
    """
    titular: str
    emissor: str
    validade_inicio: datetime
    validade_fim: datetime
    dias_para_expirar: int
    eh_icp_brasil: bool



class CertificateError(Exception):
    """Exceção para erros relacionados a certificados digitais."""
    pass


def carregar_pfx(arquivo_pfx: str, senha: str) -> bytes:
    """
    Carrega certificado PFX/PKCS#12 e retorna em formato PEM.
    
    O certificado é mantido em memória (bytes) por segurança, evitando
    salvar arquivos temporários desnecessários no disco.
    
    Args:
        arquivo_pfx: Caminho para o arquivo PFX
        senha: Senha do certificado
        
    Returns:
        bytes: Certificado e chave privada em formato PEM concatenados
        
    Raises:
        CertificateError: Se o arquivo não existir, senha estiver incorreta,
                         ou houver erro ao carregar o certificado
    """
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_pfx):
        raise CertificateError(f"Arquivo de certificado não encontrado: {arquivo_pfx}")
    
    try:
        # Ler arquivo PFX
        with open(arquivo_pfx, 'rb') as f:
            pfx_data = f.read()
        
        # Carregar PFX com pyOpenSSL
        try:
            p12 = crypto.load_pkcs12(pfx_data, senha.encode('utf-8'))
        except crypto.Error as e:
            # Erro comum: senha incorreta
            raise CertificateError(
                "Senha do certificado incorreta ou arquivo PFX inválido"
            ) from e
        
        # Extrair certificado e chave privada
        cert = p12.get_certificate()
        private_key = p12.get_privatekey()
        
        # Converter para formato PEM
        cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
        key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key)
        
        # Concatenar certificado e chave (formato esperado por signxml)
        pem_data = key_pem + cert_pem
        
        return pem_data
        
    except CertificateError:
        # Re-raise erros já tratados
        raise
    except Exception as e:
        raise CertificateError(
            f"Erro ao carregar certificado: {str(e)}"
        ) from e



def validar_certificado(arquivo_pfx: str, senha: str) -> CertificadoInfo:
    """
    Valida certificado digital e retorna suas informações.
    
    Validações realizadas:
    - Verifica se o certificado está dentro do prazo de validade
    - Verifica se é emitido pela ICP-Brasil (cadeia de certificação)
    - Exibe aviso se certificado expira em menos de 30 dias
    
    Args:
        arquivo_pfx: Caminho para o arquivo PFX
        senha: Senha do certificado
        
    Returns:
        CertificadoInfo: Informações do certificado validado
        
    Raises:
        CertificateError: Se o certificado estiver expirado ou não for ICP-Brasil
    """
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_pfx):
        raise CertificateError(f"Arquivo de certificado não encontrado: {arquivo_pfx}")
    
    try:
        # Ler arquivo PFX
        with open(arquivo_pfx, 'rb') as f:
            pfx_data = f.read()
        
        # Carregar PFX
        try:
            p12 = crypto.load_pkcs12(pfx_data, senha.encode('utf-8'))
        except crypto.Error as e:
            raise CertificateError(
                "Senha do certificado incorreta ou arquivo PFX inválido"
            ) from e
        
        cert = p12.get_certificate()
        
        # Extrair informações do certificado
        subject = cert.get_subject()
        issuer = cert.get_issuer()
        
        # Nome do titular (CN = Common Name)
        titular = subject.CN if hasattr(subject, 'CN') else "Desconhecido"
        
        # Nome do emissor
        emissor = issuer.CN if hasattr(issuer, 'CN') else "Desconhecido"
        
        # Datas de validade
        # notBefore e notAfter estão em formato bytes: YYYYMMDDHHMMSSZ
        not_before_str = cert.get_notBefore().decode('utf-8')
        not_after_str = cert.get_notAfter().decode('utf-8')
        
        # Converter para datetime
        validade_inicio = datetime.strptime(not_before_str, '%Y%m%d%H%M%SZ')
        validade_fim = datetime.strptime(not_after_str, '%Y%m%d%H%M%SZ')
        
        # Calcular dias para expirar
        agora = datetime.utcnow()
        dias_para_expirar = (validade_fim - agora).days
        
        # Verificar se certificado está expirado
        if dias_para_expirar < 0:
            raise CertificateError(
                f"Certificado expirado em {validade_fim.strftime('%d/%m/%Y')}. "
                "Por favor, renove seu certificado digital."
            )
        
        # Verificar se é ICP-Brasil
        # ICP-Brasil: verificar se a cadeia de certificação contém "AC Raiz" ou "ICP-Brasil"
        eh_icp_brasil = _verificar_icp_brasil(cert, issuer)
        
        if not eh_icp_brasil:
            raise CertificateError(
                "Certificado não é emitido pela ICP-Brasil. "
                "Apenas certificados ICP-Brasil são aceitos para emissão de NFS-e."
            )
        
        # Criar objeto com informações
        cert_info = CertificadoInfo(
            titular=titular,
            emissor=emissor,
            validade_inicio=validade_inicio,
            validade_fim=validade_fim,
            dias_para_expirar=dias_para_expirar,
            eh_icp_brasil=eh_icp_brasil
        )
        
        return cert_info
        
    except CertificateError:
        # Re-raise erros já tratados
        raise
    except Exception as e:
        raise CertificateError(
            f"Erro ao validar certificado: {str(e)}"
        ) from e


def _verificar_icp_brasil(cert, issuer) -> bool:
    """
    Verifica se o certificado é emitido pela ICP-Brasil.
    
    Verifica a cadeia de certificação procurando por indicadores
    da ICP-Brasil no emissor.
    
    Args:
        cert: Certificado X509
        issuer: Emissor do certificado
        
    Returns:
        bool: True se for ICP-Brasil, False caso contrário
    """
    # Verificar no Common Name do emissor
    emissor_cn = issuer.CN if hasattr(issuer, 'CN') else ""
    
    # Verificar no Organization do emissor
    emissor_o = issuer.O if hasattr(issuer, 'O') else ""
    
    # Verificar no Organizational Unit do emissor
    emissor_ou = issuer.OU if hasattr(issuer, 'OU') else ""
    
    # Indicadores de ICP-Brasil
    indicadores_icp = [
        'ICP-Brasil',
        'ICP Brasil',
        'AC Raiz',
        'Autoridade Certificadora Raiz',
        'ITI',
        'Instituto Nacional de Tecnologia da Informacao'
    ]
    
    # Verificar se algum indicador está presente
    texto_completo = f"{emissor_cn} {emissor_o} {emissor_ou}".upper()
    
    for indicador in indicadores_icp:
        if indicador.upper() in texto_completo:
            return True
    
    return False



def assinar_xml(xml: etree.Element, pem_data: bytes) -> etree.Element:
    """
    Assina XML com XMLDSig (enveloped signature).
    
    Usa o algoritmo rsa-sha1 conforme especificação da NFS-e.
    A assinatura é inserida como elemento filho do elemento raiz (enveloped).
    
    Args:
        xml: Elemento XML a ser assinado
        pem_data: Certificado e chave privada em formato PEM
        
    Returns:
        etree.Element: XML assinado com elemento <Signature>
        
    Raises:
        CertificateError: Se houver erro ao assinar o XML
    """
    try:
        # Criar arquivo temporário para o certificado PEM
        # (signxml requer arquivo, não aceita bytes diretamente)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False) as temp_pem:
            temp_pem.write(pem_data)
            temp_pem_path = temp_pem.name
        
        try:
            # Criar signer com algoritmo rsa-sha1
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm='rsa-sha1',
                digest_algorithm='sha1'
            )
            
            # Assinar o XML
            # O signxml espera que o elemento tenha um atributo Id para referenciar
            signed_xml = signer.sign(
                xml,
                key=temp_pem_path
            )
            
            return signed_xml
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_pem_path):
                os.remove(temp_pem_path)
                
    except Exception as e:
        raise CertificateError(
            f"Erro ao assinar XML: {str(e)}"
        ) from e



def comprimir_xml(xml: etree.Element, verbose: bool = False) -> str:
    """
    Comprime XML com Gzip e codifica em Base64.
    
    Processo:
    1. Converte XML para string
    2. Codifica string em bytes UTF-8
    3. Comprime com Gzip
    4. Codifica resultado em Base64
    
    Este é o formato esperado pela API oficial da Sefin Nacional.
    
    Args:
        xml: Elemento XML a ser comprimido
        verbose: Se True, exibe tamanhos em cada etapa
        
    Returns:
        str: XML comprimido e codificado em Base64
    """
    # 1. Converter XML para string
    xml_string = etree.tostring(
        xml,
        encoding='utf-8',
        xml_declaration=True,
        pretty_print=False
    ).decode('utf-8')
    
    tamanho_original = len(xml_string.encode('utf-8'))
    
    # 2. Comprimir com Gzip
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
        gz.write(xml_string.encode('utf-8'))
    
    xml_comprimido = buffer.getvalue()
    tamanho_comprimido = len(xml_comprimido)
    
    # 3. Codificar em Base64
    xml_base64 = base64.b64encode(xml_comprimido).decode('utf-8')
    tamanho_base64 = len(xml_base64)
    
    # Exibir tamanhos em modo verbose
    if verbose:
        print(f"📊 Tamanhos:")
        print(f"   XML original: {tamanho_original} bytes")
        print(f"   Após Gzip: {tamanho_comprimido} bytes ({tamanho_comprimido/tamanho_original*100:.1f}%)")
        print(f"   Após Base64: {tamanho_base64} bytes")
    
    return xml_base64



def descomprimir_xml(base64_data: str) -> str:
    """
    Decodifica Base64 e descomprime Gzip.
    
    Processo inverso de comprimir_xml:
    1. Decodifica Base64 para bytes
    2. Descomprime Gzip
    3. Decodifica bytes UTF-8 para string
    
    Args:
        base64_data: String em Base64 contendo XML comprimido
        
    Returns:
        str: XML descomprimido como string
        
    Raises:
        ValueError: Se os dados não estiverem em formato válido
    """
    try:
        # 1. Decodificar Base64
        xml_comprimido = base64.b64decode(base64_data)
        
        # 2. Descomprimir Gzip
        buffer = io.BytesIO(xml_comprimido)
        with gzip.GzipFile(fileobj=buffer, mode='rb') as gz:
            xml_bytes = gz.read()
        
        # 3. Decodificar UTF-8
        xml_string = xml_bytes.decode('utf-8')
        
        return xml_string
        
    except Exception as e:
        raise ValueError(
            f"Erro ao descomprimir XML: {str(e)}. "
            "Verifique se os dados estão em formato Base64+Gzip válido."
        ) from e
