"""
Módulo de construção de XML do DPS (Declaração de Prestação de Serviço).

Este módulo é responsável por construir a estrutura XML do DPS seguindo
o schema oficial v1.01 da NFS-e do Governo Federal.
"""

from lxml import etree
from typing import Optional
from datetime import datetime

from .models import Prestador, Tomador, Servico
from .config import Config


def gerar_id_dps(prestador: Prestador, config: Config) -> str:
    """
    Gera o ID do DPS conforme especificação oficial.
    
    Formato: Mun(7) + TipoInsc(1) + Insc(14) + Serie(5) + Num(15)
    
    Onde:
    - Mun: Código do município IBGE (7 dígitos)
    - TipoInsc: Tipo de inscrição (1=CNPJ, 2=CPF)
    - Insc: Inscrição (CNPJ ou CPF, completado com zeros à esquerda até 14 dígitos)
    - Serie: Série do DPS (5 dígitos, completado com zeros à esquerda)
    - Num: Número do DPS (15 dígitos, completado com zeros à esquerda)
    
    Args:
        prestador: Dados do prestador
        config: Configuração do sistema
        
    Returns:
        String com o ID do DPS (42 dígitos)
        
    Example:
        >>> prestador = Prestador(CNPJ="12345678000190", cMun="3550308")
        >>> config = Config(serie=1, proximo_numero=1)
        >>> gerar_id_dps(prestador, config)
        '35503081123456780001900000100000000000000001'
    """
    # Código do município (7 dígitos)
    mun = prestador.cMun
    
    # Tipo de inscrição e documento
    if prestador.CNPJ:
        tipo_insc = "1"
        inscricao = prestador.CNPJ.zfill(14)  # CNPJ já tem 14 dígitos
    else:
        tipo_insc = "2"
        inscricao = prestador.CPF.zfill(14)  # CPF tem 11, completar com zeros à esquerda
    
    # Série (5 dígitos)
    serie = str(config.serie).zfill(5)
    
    # Número (15 dígitos)
    numero = str(config.proximo_numero).zfill(15)
    
    # Montar ID completo
    id_dps = f"{mun}{tipo_insc}{inscricao}{serie}{numero}"
    
    return id_dps


def construir_xml_dps(
    prestador: Prestador,
    tomador: Tomador,
    servico: Servico,
    valor: float,
    data_emissao: str,
    id_dps: str,
    config: Config
) -> etree.Element:
    """
    Constrói a árvore XML do DPS seguindo o schema oficial v1.01.
    
    Estrutura completa do DPS conforme especificação:
    - Campos obrigatórios: tpAmb, dhEmi, verAplic, serie, nDPS, dCompet, tpEmit, cLocEmi
    - Estrutura completa de prestador com regTrib
    - Estrutura completa de tomador com endereço
    - Estrutura completa de serviço com locPrest e cServ
    - Valores do serviço
    
    Args:
        prestador: Dados do prestador
        tomador: Dados do tomador
        servico: Dados do serviço
        valor: Valor monetário do serviço (fornecido via CLI)
        data_emissao: Data/hora de emissão no formato ISO 8601 (fornecido via CLI)
        id_dps: ID do DPS gerado
        config: Configuração do sistema
        
    Returns:
        Elemento XML raiz do DPS
        
    Example:
        >>> xml = construir_xml_dps(prestador, tomador, servico, 1500.00, "2024-01-15T14:30:00-03:00", id_dps, config)
        >>> print(etree.tostring(xml, pretty_print=True, encoding='unicode'))
    """
    # Criar elemento raiz DPS
    dps = etree.Element("DPS", versao="1.01")
    
    # Criar infDPS com ID
    inf_dps = etree.SubElement(dps, "infDPS", Id=id_dps)
    
    # === Campos obrigatórios do DPS ===
    
    # Tipo de ambiente (1=Produção, 2=Produção Restrita)
    tp_amb = etree.SubElement(inf_dps, "tpAmb")
    tp_amb.text = "1" if config.ambiente == "producao" else "2"
    
    # Data/hora de emissão
    dh_emi = etree.SubElement(inf_dps, "dhEmi")
    dh_emi.text = data_emissao
    
    # Versão do aplicativo
    ver_aplic = etree.SubElement(inf_dps, "verAplic")
    ver_aplic.text = config.versao_aplicativo
    
    # Série do DPS
    serie_elem = etree.SubElement(inf_dps, "serie")
    serie_elem.text = str(config.serie)
    
    # Número do DPS
    n_dps = etree.SubElement(inf_dps, "nDPS")
    n_dps.text = str(config.proximo_numero)
    
    # Data de competência (extrair data da data_emissao)
    # Formato: YYYY-MM-DD
    d_compet = etree.SubElement(inf_dps, "dCompet")
    d_compet.text = data_emissao.split('T')[0]
    
    # Tipo de emitente (1=Prestador)
    tp_emit = etree.SubElement(inf_dps, "tpEmit")
    tp_emit.text = "1"
    
    # Código do local de emissão (município do prestador)
    c_loc_emi = etree.SubElement(inf_dps, "cLocEmi")
    c_loc_emi.text = prestador.cMun
    
    # === Estrutura do Prestador ===
    
    prest = etree.SubElement(inf_dps, "prest")
    
    # Documento do prestador (CNPJ ou CPF)
    if prestador.CNPJ:
        cnpj_prest = etree.SubElement(prest, "CNPJ")
        cnpj_prest.text = prestador.CNPJ
    else:
        cpf_prest = etree.SubElement(prest, "CPF")
        cpf_prest.text = prestador.CPF
    
    # Inscrição Municipal (opcional)
    if prestador.IM:
        im_prest = etree.SubElement(prest, "IM")
        im_prest.text = prestador.IM
    
    # Nome/Razão Social
    x_nome_prest = etree.SubElement(prest, "xNome")
    x_nome_prest.text = prestador.xNome
    
    # Email (opcional)
    if prestador.email:
        email_prest = etree.SubElement(prest, "email")
        email_prest.text = prestador.email
    
    # Regime Tributário (obrigatório)
    reg_trib = etree.SubElement(prest, "regTrib")
    
    op_simp_nac = etree.SubElement(reg_trib, "opSimpNac")
    op_simp_nac.text = str(prestador.regTrib.opSimpNac)
    
    # regApTribSN (opcional, apenas se opSimpNac=3)
    if prestador.regTrib.regApTribSN is not None:
        reg_ap_trib_sn = etree.SubElement(reg_trib, "regApTribSN")
        reg_ap_trib_sn.text = str(prestador.regTrib.regApTribSN)
    
    reg_esp_trib = etree.SubElement(reg_trib, "regEspTrib")
    reg_esp_trib.text = str(prestador.regTrib.regEspTrib)
    
    # === Estrutura do Tomador ===
    
    toma = etree.SubElement(inf_dps, "toma")
    
    # Documento do tomador (CNPJ ou CPF)
    if tomador.CNPJ:
        cnpj_toma = etree.SubElement(toma, "CNPJ")
        cnpj_toma.text = tomador.CNPJ
    else:
        cpf_toma = etree.SubElement(toma, "CPF")
        cpf_toma.text = tomador.CPF
    
    # Nome/Razão Social
    x_nome_toma = etree.SubElement(toma, "xNome")
    x_nome_toma.text = tomador.xNome
    
    # Email (opcional)
    if tomador.email:
        email_toma = etree.SubElement(toma, "email")
        email_toma.text = tomador.email
    
    # Endereço (opcional)
    if tomador.end:
        end = etree.SubElement(toma, "end")
        
        # Endereço nacional
        end_nac = etree.SubElement(end, "endNac")
        
        c_mun_toma = etree.SubElement(end_nac, "cMun")
        c_mun_toma.text = tomador.end.cMun
        
        cep_toma = etree.SubElement(end_nac, "CEP")
        cep_toma.text = tomador.end.CEP
        
        # Logradouro
        x_lgr = etree.SubElement(end, "xLgr")
        x_lgr.text = tomador.end.xLgr
        
        # Número
        nro = etree.SubElement(end, "nro")
        nro.text = tomador.end.nro
        
        # Bairro
        x_bairro = etree.SubElement(end, "xBairro")
        x_bairro.text = tomador.end.xBairro
    
    # === Estrutura do Serviço ===
    
    serv = etree.SubElement(inf_dps, "serv")
    
    # Local de prestação
    loc_prest = etree.SubElement(serv, "locPrest")
    c_loc_prestacao = etree.SubElement(loc_prest, "cLocPrestacao")
    c_loc_prestacao.text = servico.cLocPrestacao
    
    # Código do serviço
    c_serv = etree.SubElement(serv, "cServ")
    
    c_trib_nac = etree.SubElement(c_serv, "cTribNac")
    c_trib_nac.text = servico.cTribNac
    
    # Código de tributação municipal (opcional)
    if servico.cTribMun:
        c_trib_mun = etree.SubElement(c_serv, "cTribMun")
        c_trib_mun.text = servico.cTribMun
    
    # Descrição do serviço
    x_desc_serv = etree.SubElement(c_serv, "xDescServ")
    x_desc_serv.text = servico.xDescServ
    
    # Código NBS (opcional)
    if servico.cNBS:
        c_nbs = etree.SubElement(c_serv, "cNBS")
        c_nbs.text = servico.cNBS
    
    # === Valores do Serviço ===
    
    valores = etree.SubElement(inf_dps, "valores")
    
    # Valor do serviço (fornecido via CLI)
    v_serv = etree.SubElement(valores, "vServ")
    v_serv.text = f"{valor:.2f}"
    
    # === Grupo IBSCBS (opcional) ===
    
    if servico.ibscbs is not None:
        ibscbs = etree.SubElement(valores, "IBSCBS")
        
        # Valor do IBS (opcional)
        if servico.ibscbs.vIBS is not None:
            v_ibs = etree.SubElement(ibscbs, "vIBS")
            v_ibs.text = f"{servico.ibscbs.vIBS:.2f}"
        
        # Valor da CBS (opcional)
        if servico.ibscbs.vCBS is not None:
            v_cbs = etree.SubElement(ibscbs, "vCBS")
            v_cbs.text = f"{servico.ibscbs.vCBS:.2f}"
        
        # Alíquota do IBS (opcional)
        if servico.ibscbs.aliqIBS is not None:
            aliq_ibs = etree.SubElement(ibscbs, "aliqIBS")
            aliq_ibs.text = f"{servico.ibscbs.aliqIBS:.2f}"
        
        # Alíquota da CBS (opcional)
        if servico.ibscbs.aliqCBS is not None:
            aliq_cbs = etree.SubElement(ibscbs, "aliqCBS")
            aliq_cbs.text = f"{servico.ibscbs.aliqCBS:.2f}"
    
    return dps


def xml_para_string(xml: etree.Element) -> str:
    """
    Converte elemento XML para string formatada.
    
    Args:
        xml: Elemento XML a ser convertido
        
    Returns:
        String XML formatada com encoding UTF-8
        
    Example:
        >>> xml = etree.Element("test")
        >>> xml.text = "conteúdo"
        >>> xml_para_string(xml)
        '<?xml version="1.0" encoding="UTF-8"?>\\n<test>conteúdo</test>\\n'
    """
    return etree.tostring(
        xml,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8'
    ).decode('utf-8')
