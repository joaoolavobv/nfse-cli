"""
Módulo de validação de dados para o nfse-cli.

Este módulo contém funções de validação para documentos, códigos,
valores e regras de negócio da NFS-e.
"""

from typing import List, Optional
from datetime import datetime
import re


class ValidationError(Exception):
    """Exceção para erros de validação de dados."""
    pass


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida formato e dígito verificador de CNPJ.
    
    Args:
        cnpj: String contendo o CNPJ (apenas dígitos)
        
    Returns:
        True se o CNPJ é válido, False caso contrário
        
    Raises:
        ValidationError: Se o formato é inválido
    """
    # Remove caracteres não numéricos
    cnpj_limpo = re.sub(r'\D', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj_limpo) != 14:
        raise ValidationError(f"CNPJ deve ter 14 dígitos. Recebido: {len(cnpj_limpo)} dígitos")
    
    # Verifica se não são todos dígitos iguais
    if cnpj_limpo == cnpj_limpo[0] * 14:
        raise ValidationError("CNPJ não pode ter todos os dígitos iguais")
    
    # Calcula primeiro dígito verificador
    soma = 0
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(12):
        soma += int(cnpj_limpo[i]) * peso[i]
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj_limpo[12]) != digito1:
        raise ValidationError(f"CNPJ '{cnpj}' possui dígito verificador inválido")
    
    # Calcula segundo dígito verificador
    soma = 0
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(13):
        soma += int(cnpj_limpo[i]) * peso[i]
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj_limpo[13]) != digito2:
        raise ValidationError(f"CNPJ '{cnpj}' possui dígito verificador inválido")
    
    return True


def validar_cpf(cpf: str) -> bool:
    """
    Valida formato e dígito verificador de CPF.
    
    Args:
        cpf: String contendo o CPF (apenas dígitos)
        
    Returns:
        True se o CPF é válido, False caso contrário
        
    Raises:
        ValidationError: Se o formato é inválido
    """
    # Remove caracteres não numéricos
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf_limpo) != 11:
        raise ValidationError(f"CPF deve ter 11 dígitos. Recebido: {len(cpf_limpo)} dígitos")
    
    # Verifica se não são todos dígitos iguais
    if cpf_limpo == cpf_limpo[0] * 11:
        raise ValidationError("CPF não pode ter todos os dígitos iguais")
    
    # Calcula primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf_limpo[i]) * (10 - i)
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[9]) != digito1:
        raise ValidationError(f"CPF '{cpf}' possui dígito verificador inválido")
    
    # Calcula segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf_limpo[i]) * (11 - i)
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[10]) != digito2:
        raise ValidationError(f"CPF '{cpf}' possui dígito verificador inválido")
    
    return True


def validar_codigo_municipio(codigo: str) -> bool:
    """
    Valida formato de código de município IBGE.
    
    Args:
        codigo: String contendo o código do município
        
    Returns:
        True se o código é válido, False caso contrário
        
    Raises:
        ValidationError: Se o formato é inválido
    """
    # Remove caracteres não numéricos
    codigo_limpo = re.sub(r'\D', '', codigo)
    
    # Verifica se tem exatamente 7 dígitos
    if len(codigo_limpo) != 7:
        raise ValidationError(
            f"Código de município deve ter exatamente 7 dígitos. Recebido: {len(codigo_limpo)} dígitos"
        )
    
    return True


def validar_codigo_tributacao(codigo: str) -> bool:
    """
    Valida formato de código de tributação nacional.
    
    Args:
        codigo: String contendo o código de tributação
        
    Returns:
        True se o código é válido, False caso contrário
        
    Raises:
        ValidationError: Se o formato é inválido
    """
    # Remove caracteres não numéricos
    codigo_limpo = re.sub(r'\D', '', codigo)
    
    # Verifica se tem exatamente 6 dígitos
    if len(codigo_limpo) != 6:
        raise ValidationError(
            f"Código de tributação nacional deve ter exatamente 6 dígitos numéricos. "
            f"Recebido: {len(codigo_limpo)} dígitos (ex: 010101)"
        )
    
    return True


def validar_valor(valor: float) -> bool:
    """
    Valida que o valor é positivo.
    
    Args:
        valor: Valor monetário a ser validado
        
    Returns:
        True se o valor é válido, False caso contrário
        
    Raises:
        ValidationError: Se o valor não é positivo
    """
    if valor <= 0:
        raise ValidationError(f"Valor deve ser positivo (maior que zero). Recebido: {valor}")
    
    return True


def validar_data_iso(data: str) -> bool:
    """
    Valida formato de data e verifica se é uma data real.
    
    Formatos aceitos:
    - YYYY-MM-DD (ex: 2024-01-15)
    - DD/MM/YYYY (ex: 15/01/2024)
    
    Args:
        data: String contendo a data em um dos formatos aceitos
        
    Returns:
        True se a data é válida, False caso contrário
        
    Raises:
        ValidationError: Se o formato é inválido ou a data não é real
    """
    # Formatos aceitos
    formatos = [
        ('%Y-%m-%d', 'YYYY-MM-DD'),      # 2024-01-15
        ('%d/%m/%Y', 'DD/MM/YYYY'),      # 15/01/2024
    ]
    
    for formato, exemplo in formatos:
        try:
            # Tenta fazer o parsing da data
            data_obj = datetime.strptime(data, formato)
            
            # Valida se a data parseada corresponde à string original
            # Isso evita casos como 31/02/2024 que o strptime pode aceitar
            if data_obj.strftime(formato) != data:
                continue
                
            return True
        except ValueError:
            continue
    
    raise ValidationError(
        f"Data deve estar em um dos formatos: YYYY-MM-DD ou DD/MM/YYYY. "
        f"Exemplos: 2024-01-15 ou 15/01/2024. Recebido: {data}"
    )


def converter_data_para_iso8601(data: str) -> str:
    """
    Converte data do formato aceito pelo usuário para ISO 8601 com hora.
    
    Formatos de entrada aceitos:
    - YYYY-MM-DD (ex: 2024-01-15)
    - DD/MM/YYYY (ex: 15/01/2024)
    
    Formato de saída:
    - YYYY-MM-DDTHH:MM:SS-03:00 (ex: 2024-01-15T00:00:00-03:00)
    
    Args:
        data: String contendo a data em um dos formatos aceitos
        
    Returns:
        String com a data no formato ISO 8601 com hora (00:00:00) e timezone (-03:00)
        
    Raises:
        ValidationError: Se o formato é inválido ou a data não é real
        
    Example:
        >>> converter_data_para_iso8601("2024-01-15")
        '2024-01-15T00:00:00-03:00'
        >>> converter_data_para_iso8601("15/01/2024")
        '2024-01-15T00:00:00-03:00'
    """
    # Formatos aceitos
    formatos = [
        '%Y-%m-%d',      # 2024-01-15
        '%d/%m/%Y',      # 15/01/2024
    ]
    
    data_obj = None
    for formato in formatos:
        try:
            # Tenta fazer o parsing da data
            data_obj = datetime.strptime(data, formato)
            
            # Valida se a data parseada corresponde à string original
            if data_obj.strftime(formato) != data:
                continue
                
            break
        except ValueError:
            continue
    
    if data_obj is None:
        raise ValidationError(
            f"Data deve estar em um dos formatos: YYYY-MM-DD ou DD/MM/YYYY. "
            f"Exemplos: 2024-01-15 ou 15/01/2024. Recebido: {data}"
        )
    
    # Converter para ISO 8601 com hora 00:00:00 e timezone -03:00
    return data_obj.strftime('%Y-%m-%dT00:00:00-03:00')


# Códigos de serviço com exceção à regra de alíquota mínima de 2%
CODIGOS_EXCECAO_ALIQUOTA_MINIMA = {
    '042201', '042301', '050901', '070201', '070202', '070501', '070502',
    '090201', '090202', '100101', '100102', '100103', '100104', '100105',
    '100201', '100202', '100301', '100401', '100402', '100403', '100501',
    '100502', '100601', '100701', '100801', '100901', '101001', '150101',
    '150102', '150103', '150104', '150105', '151001', '151002', '151003',
    '151004', '151005', '160101', '160102', '160103', '160104', '160201',
    '170501', '170601', '171001', '171002', '171101', '171102', '171201',
    '210101', '250301'
}


def validar_aliquota_maxima(aliquota: float) -> bool:
    """
    Valida que a alíquota não ultrapassa 5%.
    
    Args:
        aliquota: Alíquota em percentual (ex: 5.0 para 5%)
        
    Returns:
        True se a alíquota é válida, False caso contrário
        
    Raises:
        ValidationError: Se a alíquota ultrapassa 5%
    """
    if aliquota > 5.0:
        raise ValidationError(
            f"Não é permitido informar alíquota aplicada superior a 5%. Recebido: {aliquota}%"
        )
    
    return True


def validar_aliquota_minima(aliquota: float, codigo_servico: str) -> bool:
    """
    Valida que a alíquota não é inferior a 2% (com exceções).
    
    Args:
        aliquota: Alíquota em percentual (ex: 2.0 para 2%)
        codigo_servico: Código de tributação nacional do serviço
        
    Returns:
        True se a alíquota é válida, False caso contrário
        
    Raises:
        ValidationError: Se a alíquota é inferior a 2% e não há exceção
    """
    # Remove caracteres não numéricos do código
    codigo_limpo = re.sub(r'\D', '', codigo_servico)
    
    # Verifica se o código tem exceção à regra de 2%
    if codigo_limpo in CODIGOS_EXCECAO_ALIQUOTA_MINIMA:
        return True
    
    # Para códigos sem exceção, valida alíquota mínima de 2%
    if aliquota < 2.0:
        raise ValidationError(
            f"Alíquota não pode ser inferior a 2% para o código de serviço {codigo_servico}. "
            f"Recebido: {aliquota}%"
        )
    
    return True


# Códigos de serviço com incidência no local da prestação
CODIGOS_INCIDENCIA_LOCAL_PRESTACAO = {
    '030401', '030402', '030403', '030501', '070201', '070202', '070401',
    '070501', '070502', '070901', '070902', '071001', '071002', '071101',
    '071102', '071201', '071601', '071701', '071801', '071901', '110101',
    '110102', '110201', '110301', '110401', '110402', '120101', '120201',
    '120301', '120401', '120501', '120601', '120701', '120801', '120901',
    '121001', '121101', '121201', '121301', '121401', '121501', '121601',
    '121701', '160101', '160102', '160103', '160104', '160201', '171001',
    '171002', '220101'
}


def validar_local_incidencia(
    codigo_servico: str,
    c_loc_incid: str,
    c_loc_prestacao: str,
    c_mun_prestador: str,
    c_mun_tomador: str
) -> bool:
    """
    Valida regras de incidência do ISSQN baseadas no código de serviço.
    
    Args:
        codigo_servico: Código de tributação nacional do serviço
        c_loc_incid: Código do local de incidência do ISSQN
        c_loc_prestacao: Código do município onde o serviço foi prestado
        c_mun_prestador: Código do município do prestador
        c_mun_tomador: Código do município do tomador
        
    Returns:
        True se a regra de incidência é válida, False caso contrário
        
    Raises:
        ValidationError: Se a regra de incidência não é respeitada
    """
    # Remove caracteres não numéricos do código
    codigo_limpo = re.sub(r'\D', '', codigo_servico)
    
    # Regra 1: Incidência no domicílio do tomador (código 170501)
    if codigo_limpo == '170501':
        if c_loc_incid != c_mun_tomador:
            raise ValidationError(
                f"Para o código de serviço {codigo_servico}, o local de incidência (cLocIncid) "
                f"deve ser igual ao município do tomador. "
                f"Esperado: {c_mun_tomador}, Recebido: {c_loc_incid}"
            )
        return True
    
    # Regra 2: Incidência no local da prestação (códigos específicos)
    if codigo_limpo in CODIGOS_INCIDENCIA_LOCAL_PRESTACAO:
        if c_loc_incid != c_loc_prestacao:
            raise ValidationError(
                f"Para o código de serviço {codigo_servico}, o local de incidência (cLocIncid) "
                f"deve ser igual ao local da prestação (cLocPrestacao). "
                f"Esperado: {c_loc_prestacao}, Recebido: {c_loc_incid}"
            )
        return True
    
    # Regra 3: Incidência no estabelecimento do prestador (demais códigos)
    if c_loc_incid != c_mun_prestador:
        raise ValidationError(
            f"Para o código de serviço {codigo_servico}, o local de incidência (cLocIncid) "
            f"deve ser igual ao município do prestador. "
            f"Esperado: {c_mun_prestador}, Recebido: {c_loc_incid}"
        )
    
    return True



def validar_obrigatoriedade_ibscbs(
    prestador_regime: 'RegimeTributario',
    data_competencia: str,
    ibscbs_presente: bool
) -> bool:
    """
    Valida se o grupo IBSCBS é obrigatório baseado no regime tributário e data de competência.
    
    Regras:
    - Opcional para optantes do Simples Nacional (opSimpNac=2 ou 3) até 31/12/2026
    - Obrigatório para não optantes do Simples Nacional (opSimpNac=1)
    - Obrigatório para todos a partir de 01/01/2027
    
    Args:
        prestador_regime: Regime tributário do prestador
        data_competencia: Data de competência no formato YYYY-MM-DD
        ibscbs_presente: Se o grupo IBSCBS foi fornecido
        
    Returns:
        True se a validação passa, False caso contrário
        
    Raises:
        ValidationError: Se IBSCBS é obrigatório mas não foi fornecido
    """
    from datetime import datetime
    
    # Converter data de competência para datetime
    try:
        data_comp = datetime.strptime(data_competencia, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(f"Data de competência inválida: {data_competencia}")
    
    # Data limite: 01/01/2027
    data_limite = datetime(2027, 1, 1)
    
    # A partir de 01/01/2027, IBSCBS é obrigatório para todos
    if data_comp >= data_limite:
        if not ibscbs_presente:
            raise ValidationError(
                "O grupo IBSCBS é obrigatório para todos os prestadores a partir de 01/01/2027. "
                "Por favor, inclua as informações de IBS/CBS no arquivo JSON do serviço."
            )
        return True
    
    # Antes de 01/01/2027, verificar regime tributário
    # opSimpNac: 1=Não Optante, 2=MEI, 3=ME/EPP
    if prestador_regime.opSimpNac == 1:  # Não optante do Simples Nacional
        if not ibscbs_presente:
            raise ValidationError(
                "O grupo IBSCBS é obrigatório para prestadores não optantes do Simples Nacional. "
                "Por favor, inclua as informações de IBS/CBS no arquivo JSON do serviço."
            )
    
    # Para optantes do Simples Nacional (opSimpNac=2 ou 3), IBSCBS é opcional até 2027
    return True
