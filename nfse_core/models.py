"""
Módulo de modelos de dados para o nfse-cli.

Este módulo define as estruturas de dados (dataclasses) usadas pelo sistema,
incluindo validações de campos obrigatórios e formatos.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime
import json
import os
import re


@dataclass
class Endereco:
    """
    Endereço do tomador.
    
    Corresponde às tags XML:
    - xLgr: Logradouro
    - nro: Número
    - xBairro: Bairro
    - cMun: Código do município IBGE (7 dígitos)
    - CEP: CEP (8 dígitos)
    """
    xLgr: str = ""
    nro: str = ""
    xBairro: str = ""
    cMun: str = ""
    CEP: str = ""
    
    def validar(self) -> List[str]:
        """
        Valida os dados do endereço.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        if not self.xLgr:
            erros.append("Campo 'xLgr' (logradouro) é obrigatório")
        
        if not self.nro:
            erros.append("Campo 'nro' (número) é obrigatório")
        
        if not self.xBairro:
            erros.append("Campo 'xBairro' (bairro) é obrigatório")
        
        if not self.cMun:
            erros.append("Campo 'cMun' (código do município) é obrigatório")
        elif len(self.cMun) != 7 or not self.cMun.isdigit():
            erros.append(f"Campo 'cMun' deve ter exatamente 7 dígitos numéricos, recebido: '{self.cMun}'")
        
        if not self.CEP:
            erros.append("Campo 'CEP' é obrigatório")
        elif len(self.CEP) != 8 or not self.CEP.isdigit():
            erros.append(f"Campo 'CEP' deve ter exatamente 8 dígitos numéricos, recebido: '{self.CEP}'")
        
        return erros



@dataclass
class RegimeTributario:
    """
    Regime tributário do prestador.
    
    Corresponde às tags XML:
    - opSimpNac: Opção pelo Simples Nacional
      * 1 = Não Optante
      * 2 = MEI (Microempreendedor Individual)
      * 3 = ME/EPP (Microempresa ou Empresa de Pequeno Porte)
    - regEspTrib: Regime Especial de Tributação
      * 0 = Nenhum
      * 1-6 = Regimes especiais específicos
      * 9 = Outros
    - regApTribSN: Regime de Apuração (opcional, apenas se opSimpNac=3)
      * 1, 2 ou 3
    """
    opSimpNac: int = 0
    regEspTrib: int = 0
    regApTribSN: Optional[int] = None
    
    def validar(self) -> List[str]:
        """
        Valida os dados do regime tributário.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        # Validar opSimpNac
        if self.opSimpNac not in [1, 2, 3]:
            erros.append(f"Campo 'opSimpNac' deve ser 1, 2 ou 3, recebido: {self.opSimpNac}")
        
        # Validar regEspTrib
        valores_validos_reg_esp = [0, 1, 2, 3, 4, 5, 6, 9]
        if self.regEspTrib not in valores_validos_reg_esp:
            erros.append(f"Campo 'regEspTrib' deve ser 0, 1-6 ou 9, recebido: {self.regEspTrib}")
        
        # Validar regApTribSN
        if self.regApTribSN is not None:
            if self.opSimpNac != 3:
                erros.append(f"Campo 'regApTribSN' só é permitido quando 'opSimpNac' é 3, mas opSimpNac={self.opSimpNac}")
            elif self.regApTribSN not in [1, 2, 3]:
                erros.append(f"Campo 'regApTribSN' deve ser 1, 2 ou 3, recebido: {self.regApTribSN}")
        
        return erros



@dataclass
class Prestador:
    """
    Dados do prestador de serviço (empresa ou profissional que emite a nota).
    
    Corresponde às tags XML:
    - CNPJ ou CPF: Documento do prestador (um dos dois é obrigatório)
    - xNome: Nome ou razão social
    - cMun: Código do município IBGE (7 dígitos)
    - IM: Inscrição Municipal (opcional)
    - email: Email (opcional)
    - regTrib: Regime tributário (obrigatório)
    """
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    xNome: str = ""
    cMun: str = ""
    IM: Optional[str] = None
    email: Optional[str] = None
    regTrib: Optional[RegimeTributario] = None
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Prestador':
        """
        Carrega prestador de arquivo JSON.
        
        Args:
            caminho: Caminho relativo ao arquivo JSON
            
        Returns:
            Instância de Prestador
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            json.JSONDecodeError: Se o JSON for inválido
        """
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Converter regTrib de dict para RegimeTributario se presente
        if 'regTrib' in dados and isinstance(dados['regTrib'], dict):
            dados['regTrib'] = RegimeTributario(**dados['regTrib'])
        
        return cls(**dados)
    
    def salvar(self, caminho: str):
        """
        Salva prestador em arquivo JSON.
        
        Args:
            caminho: Caminho onde salvar o arquivo JSON
        """
        # Criar diretório se não existir
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Converter para dict
        dados = asdict(self)
        
        # Salvar com formatação
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    
    def validar(self) -> List[str]:
        """
        Valida os dados do prestador.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        # Validar documento (CNPJ ou CPF obrigatório)
        if not self.CNPJ and not self.CPF:
            erros.append("Campo 'CNPJ' ou 'CPF' é obrigatório")
        
        if self.CNPJ and self.CPF:
            erros.append("Apenas um dos campos 'CNPJ' ou 'CPF' deve ser fornecido")
        
        # Validar formato de CNPJ
        if self.CNPJ:
            if len(self.CNPJ) != 14 or not self.CNPJ.isdigit():
                erros.append(f"Campo 'CNPJ' deve ter exatamente 14 dígitos numéricos, recebido: '{self.CNPJ}'")
        
        # Validar formato de CPF
        if self.CPF:
            if len(self.CPF) != 11 or not self.CPF.isdigit():
                erros.append(f"Campo 'CPF' deve ter exatamente 11 dígitos numéricos, recebido: '{self.CPF}'")
        
        # Validar xNome
        if not self.xNome:
            erros.append("Campo 'xNome' (nome/razão social) é obrigatório")
        
        # Validar cMun
        if not self.cMun:
            erros.append("Campo 'cMun' (código do município) é obrigatório")
        elif len(self.cMun) != 7 or not self.cMun.isdigit():
            erros.append(f"Campo 'cMun' deve ter exatamente 7 dígitos numéricos, recebido: '{self.cMun}'")
        
        # Validar regTrib (obrigatório)
        if self.regTrib is None:
            erros.append("Campo 'regTrib' (regime tributário) é obrigatório")
        else:
            # Validar campos do regime tributário
            erros_regime = self.regTrib.validar()
            erros.extend([f"regTrib: {erro}" for erro in erros_regime])
        
        return erros
    
    def obter_documento(self) -> str:
        """
        Retorna CNPJ ou CPF do prestador.
        
        Returns:
            String com o documento (CNPJ ou CPF)
        """
        return self.CNPJ or self.CPF or ""



@dataclass
class Tomador:
    """
    Dados do tomador de serviço (cliente que contrata o serviço).
    
    Corresponde às tags XML:
    - CNPJ ou CPF: Documento do tomador (um dos dois é obrigatório)
    - xNome: Nome ou razão social
    - email: Email (opcional)
    - end: Endereço (opcional)
    """
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    xNome: str = ""
    email: Optional[str] = None
    end: Optional[Endereco] = None
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Tomador':
        """
        Carrega tomador de arquivo JSON.
        
        Args:
            caminho: Caminho relativo ao arquivo JSON
            
        Returns:
            Instância de Tomador
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            json.JSONDecodeError: Se o JSON for inválido
        """
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Converter end de dict para Endereco se presente
        if 'end' in dados and isinstance(dados['end'], dict):
            dados['end'] = Endereco(**dados['end'])
        
        return cls(**dados)
    
    def salvar(self, caminho: str):
        """
        Salva tomador em arquivo JSON.
        
        Args:
            caminho: Caminho onde salvar o arquivo JSON
        """
        # Criar diretório se não existir
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Converter para dict
        dados = asdict(self)
        
        # Salvar com formatação
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    
    def validar(self) -> List[str]:
        """
        Valida os dados do tomador.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        # Validar documento (CNPJ ou CPF obrigatório)
        if not self.CNPJ and not self.CPF:
            erros.append("Campo 'CNPJ' ou 'CPF' é obrigatório")
        
        if self.CNPJ and self.CPF:
            erros.append("Apenas um dos campos 'CNPJ' ou 'CPF' deve ser fornecido")
        
        # Validar formato de CNPJ
        if self.CNPJ:
            if len(self.CNPJ) != 14 or not self.CNPJ.isdigit():
                erros.append(f"Campo 'CNPJ' deve ter exatamente 14 dígitos numéricos, recebido: '{self.CNPJ}'")
        
        # Validar formato de CPF
        if self.CPF:
            if len(self.CPF) != 11 or not self.CPF.isdigit():
                erros.append(f"Campo 'CPF' deve ter exatamente 11 dígitos numéricos, recebido: '{self.CPF}'")
        
        # Validar xNome
        if not self.xNome:
            erros.append("Campo 'xNome' (nome/razão social) é obrigatório")
        
        # Validar endereço se presente
        if self.end is not None:
            erros_endereco = self.end.validar()
            erros.extend([f"end: {erro}" for erro in erros_endereco])
        
        return erros
    
    def obter_documento(self) -> str:
        """
        Retorna CNPJ ou CPF do tomador.
        
        Returns:
            String com o documento (CNPJ ou CPF)
        """
        return self.CNPJ or self.CPF or ""


@dataclass
class IBSCBS:
    """
    Informações do IBS (Imposto sobre Bens e Serviços) e CBS (Contribuição sobre Bens e Serviços).
    
    Grupo opcional até 01/01/2027 para optantes do Simples Nacional.
    Obrigatório para não optantes do Simples Nacional.
    Obrigatório para todos a partir de 01/01/2027.
    
    Corresponde às tags XML:
    - vIBS: Valor do IBS
    - vCBS: Valor da CBS
    - aliqIBS: Alíquota do IBS em percentual (opcional)
    - aliqCBS: Alíquota da CBS em percentual (opcional)
    """
    vIBS: Optional[float] = None
    vCBS: Optional[float] = None
    aliqIBS: Optional[float] = None
    aliqCBS: Optional[float] = None
    
    def validar(self) -> List[str]:
        """
        Valida os dados do IBSCBS.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        # Se IBSCBS está presente, pelo menos vIBS ou vCBS deve estar presente
        if self.vIBS is None and self.vCBS is None:
            erros.append("Pelo menos um dos campos 'vIBS' ou 'vCBS' deve ser informado no grupo IBSCBS")
        
        # Validar valores não negativos
        if self.vIBS is not None and self.vIBS < 0:
            erros.append(f"Campo 'vIBS' não pode ser negativo, recebido: {self.vIBS}")
        
        if self.vCBS is not None and self.vCBS < 0:
            erros.append(f"Campo 'vCBS' não pode ser negativo, recebido: {self.vCBS}")
        
        # Validar alíquotas se presentes
        if self.aliqIBS is not None and (self.aliqIBS < 0 or self.aliqIBS > 100):
            erros.append(f"Campo 'aliqIBS' deve estar entre 0 e 100, recebido: {self.aliqIBS}")
        
        if self.aliqCBS is not None and (self.aliqCBS < 0 or self.aliqCBS > 100):
            erros.append(f"Campo 'aliqCBS' deve estar entre 0 e 100, recebido: {self.aliqCBS}")
        
        return erros


@dataclass
class Servico:
    """
    Dados do serviço prestado.
    
    Corresponde às tags XML:
    - xDescServ: Descrição completa do serviço
    - cTribNac: Código de tributação nacional (6 dígitos numéricos)
    - cLocPrestacao: Código do município IBGE onde o serviço foi prestado (7 dígitos)
    - cTribMun: Código de tributação municipal (3 dígitos, opcional)
    - cNBS: Código NBS (opcional)
    - cIntContrib: Código interno do contribuinte (opcional)
    - aliquota: Alíquota do ISSQN em percentual (opcional, ex: 5.0 para 5%)
    - ibscbs: Informações de IBS/CBS (opcional)
    
    IMPORTANTE: Este modelo NÃO contém os campos vServ (valor) ou dhEmi (data/hora),
    pois estes devem ser fornecidos via linha de comando no momento da emissão.
    """
    xDescServ: str = ""
    cTribNac: str = ""
    cLocPrestacao: str = ""
    cTribMun: Optional[str] = None
    cNBS: Optional[str] = None
    cIntContrib: Optional[str] = None
    aliquota: Optional[float] = None
    ibscbs: Optional[IBSCBS] = None
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Servico':
        """
        Carrega serviço de arquivo JSON.
        
        Args:
            caminho: Caminho relativo ao arquivo JSON
            
        Returns:
            Instância de Servico
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            json.JSONDecodeError: Se o JSON for inválido
        """
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Verificar se contém campos proibidos
        if 'vServ' in dados:
            raise ValueError("Campo 'vServ' não deve estar no arquivo JSON do serviço. Use o parâmetro --valor na linha de comando.")
        
        if 'dhEmi' in dados:
            raise ValueError("Campo 'dhEmi' não deve estar no arquivo JSON do serviço. Use o parâmetro --data na linha de comando.")
        
        # Converter IBSCBS de dict para objeto se presente
        if 'ibscbs' in dados and dados['ibscbs'] is not None:
            dados['ibscbs'] = IBSCBS(**dados['ibscbs'])
        
        return cls(**dados)
    
    def salvar(self, caminho: str):
        """
        Salva serviço em arquivo JSON.
        
        Args:
            caminho: Caminho onde salvar o arquivo JSON
        """
        # Criar diretório se não existir
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Converter para dict
        dados = asdict(self)
        
        # Salvar com formatação
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    
    def validar(self) -> List[str]:
        """
        Valida os dados do serviço.
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        from .validation import validar_aliquota_maxima, validar_aliquota_minima, ValidationError
        
        erros = []
        
        # Validar xDescServ
        if not self.xDescServ:
            erros.append("Campo 'xDescServ' (descrição do serviço) é obrigatório")
        
        # Validar cTribNac
        if not self.cTribNac:
            erros.append("Campo 'cTribNac' (código de tributação nacional) é obrigatório")
        elif len(self.cTribNac) != 6 or not self.cTribNac.isdigit():
            erros.append(f"Campo 'cTribNac' deve ter exatamente 6 dígitos numéricos, recebido: '{self.cTribNac}'")
        
        # Validar cLocPrestacao
        if not self.cLocPrestacao:
            erros.append("Campo 'cLocPrestacao' (código do local de prestação) é obrigatório")
        elif len(self.cLocPrestacao) != 7 or not self.cLocPrestacao.isdigit():
            erros.append(f"Campo 'cLocPrestacao' deve ter exatamente 7 dígitos numéricos, recebido: '{self.cLocPrestacao}'")
        
        # Validar cTribMun se presente
        if self.cTribMun is not None:
            if len(self.cTribMun) != 3 or not self.cTribMun.isdigit():
                erros.append(f"Campo 'cTribMun' deve ter exatamente 3 dígitos numéricos, recebido: '{self.cTribMun}'")
        
        # Validar alíquota se presente
        if self.aliquota is not None:
            try:
                validar_aliquota_maxima(self.aliquota)
            except ValidationError as e:
                erros.append(str(e))
            
            try:
                validar_aliquota_minima(self.aliquota, self.cTribNac)
            except ValidationError as e:
                erros.append(str(e))
        
        # Validar IBSCBS se presente
        if self.ibscbs is not None:
            erros_ibscbs = self.ibscbs.validar()
            erros.extend(erros_ibscbs)
        
        return erros
