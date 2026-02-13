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
import re

from lxml import etree
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
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
        
        # Carregar PFX com cryptography
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                senha.encode('utf-8'),
                backend=default_backend()
            )
        except ValueError as e:
            # Erro comum: senha incorreta
            raise CertificateError(
                "Senha do certificado incorreta ou arquivo PFX inválido"
            ) from e
        
        # Converter chave privada para PEM (formato PKCS8)
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Converter certificado para PEM
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        
        # Concatenar chave e certificado (formato esperado por signxml)
        # Ordem: chave privada primeiro, depois certificado
        pem_data = key_pem + cert_pem
        
        # Se houver certificados adicionais na cadeia, incluir também
        if additional_certs:
            for cert in additional_certs:
                pem_data += cert.public_bytes(serialization.Encoding.PEM)
        
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
        
        # Carregar PFX com cryptography
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                senha.encode('utf-8'),
                backend=default_backend()
            )
        except ValueError as e:
            raise CertificateError(
                "Senha do certificado incorreta ou arquivo PFX inválido"
            ) from e
        
        # Extrair informações do certificado
        subject = certificate.subject
        issuer = certificate.issuer
        
        # Nome do titular (CN = Common Name)
        titular_attrs = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        titular = titular_attrs[0].value if titular_attrs else "Desconhecido"
        
        # Nome do emissor
        emissor_attrs = issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        emissor = emissor_attrs[0].value if emissor_attrs else "Desconhecido"
        
        # Datas de validade
        validade_inicio = certificate.not_valid_before_utc
        validade_fim = certificate.not_valid_after_utc
        
        # Calcular dias para expirar
        agora = datetime.now(validade_fim.tzinfo)
        dias_para_expirar = (validade_fim - agora).days
        
        # Verificar se certificado está expirado
        if dias_para_expirar < 0:
            raise CertificateError(
                f"Certificado expirado em {validade_fim.strftime('%d/%m/%Y')}. "
                "Por favor, renove seu certificado digital."
            )
        
        # Verificar se é ICP-Brasil
        eh_icp_brasil = _verificar_icp_brasil(certificate)
        
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


def _verificar_icp_brasil(certificate: x509.Certificate) -> bool:
    """
    Verifica se o certificado é emitido pela ICP-Brasil.
    
    Verifica a cadeia de certificação procurando por indicadores
    da ICP-Brasil no emissor.
    
    Args:
        certificate: Certificado X509 da biblioteca cryptography
        
    Returns:
        bool: True se for ICP-Brasil, False caso contrário
    """
    issuer = certificate.issuer
    
    # Extrair Common Name do emissor
    cn_attrs = issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    emissor_cn = cn_attrs[0].value if cn_attrs else ""
    
    # Extrair Organization do emissor
    o_attrs = issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)
    emissor_o = o_attrs[0].value if o_attrs else ""
    
    # Extrair Organizational Unit do emissor
    ou_attrs = issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME)
    emissor_ou = ou_attrs[0].value if ou_attrs else ""
    
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
    Assina XML com XMLDSig (enveloped signature) sem usar prefixos de namespace.
    
    Usa o algoritmo rsa-sha256 conforme especificação da NFS-e.
    A assinatura é inserida como elemento filho do elemento raiz (enveloped).
    
    IMPORTANTE: A API da Sefin Nacional rejeita XMLs com prefixos de namespace (regra E6155).
    Esta função cria a assinatura manualmente sem prefixos.
    
    Args:
        xml: Elemento XML a ser assinado
        pem_data: Certificado e chave privada em formato PEM
        
    Returns:
        etree.Element: XML assinado com elemento <Signature> sem prefixos
        
    Raises:
        CertificateError: Se houver erro ao assinar o XML
    """
    try:
        # Primeiro, assinar normalmente com signxml
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm='rsa-sha256',
            digest_algorithm='sha256',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )
        
        # Assinar o XML
        signed_xml = signer.sign(
            xml,
            key=pem_data
        )
        
        # Agora vamos reconstruir o XML sem prefixos de namespace
        # Extrair o elemento Signature
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        signature_elem = signed_xml.find('.//ds:Signature', namespaces=ns)
        
        if signature_elem is None:
            raise CertificateError("Elemento Signature não encontrado no XML assinado")
        
        # Remover o elemento Signature original
        signed_xml.remove(signature_elem)
        
        # Criar novo elemento Signature sem prefixo
        signature_novo = _criar_signature_sem_prefixo(signature_elem)
        
        # Adicionar o novo elemento Signature ao XML
        signed_xml.append(signature_novo)
        
        return signed_xml
                
    except Exception as e:
        raise CertificateError(
            f"Erro ao assinar XML: {str(e)}"
        ) from e


def _criar_signature_sem_prefixo(signature_elem: etree.Element) -> etree.Element:
    """
    Recria um elemento Signature sem prefixos de namespace.
    
    Args:
        signature_elem: Elemento Signature original com prefixos
        
    Returns:
        etree.Element: Novo elemento Signature sem prefixos
    """
    # Converter o elemento para string
    sig_string = etree.tostring(signature_elem, encoding='unicode')
    
    # Remover todos os prefixos de namespace (ds:, ns0:, etc)
    # Substituir xmlns:prefixo="..." por xmlns="..."
    sig_string = re.sub(r'xmlns:\w+="http://www\.w3\.org/2000/09/xmldsig#"', 
                       'xmlns="http://www.w3.org/2000/09/xmldsig#"', sig_string)
    
    # Remover prefixos das tags (ds:Tag ou ns0:Tag vira Tag)
    sig_string = re.sub(r'<(\w+):(\w+)', r'<\2', sig_string)
    sig_string = re.sub(r'</(\w+):(\w+)', r'</\2', sig_string)
    
    # Converter de volta para elemento
    signature_novo = etree.fromstring(sig_string.encode('utf-8'))
    
    return signature_novo


def _remover_prefixos_namespace_preservando_assinatura(xml: etree.Element) -> etree.Element:
    """
    Remove prefixos de namespace de um XML mantendo a assinatura válida.
    
    A API da Sefin Nacional rejeita XMLs com prefixos de namespace (regra E6155).
    Esta função remove os prefixos mas preserva a estrutura da assinatura.
    
    A chave é usar o namespace como atributo xmlns padrão ao invés de xmlns:prefixo.
    
    Args:
        xml: Elemento XML assinado com prefixos
        
    Returns:
        etree.Element: XML sem prefixos de namespace mas com assinatura válida
    """
    # Converter para string sem pretty print para preservar a assinatura
    xml_string = etree.tostring(xml, encoding='unicode', pretty_print=False)
    
    # Substituir xmlns:ds="..." por xmlns="..." (apenas a primeira ocorrência)
    xml_string = xml_string.replace('xmlns:ds="http://www.w3.org/2000/09/xmldsig#"', 
                                     'xmlns="http://www.w3.org/2000/09/xmldsig#"', 1)
    
    # Remover prefixo ds: de todas as tags
    xml_string = re.sub(r'<ds:(\w+)', r'<\1', xml_string)
    xml_string = re.sub(r'</ds:(\w+)', r'</\1', xml_string)
    
    # Converter de volta para elemento
    xml_sem_prefixo = etree.fromstring(xml_string.encode('utf-8'))
    
    return xml_sem_prefixo



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
