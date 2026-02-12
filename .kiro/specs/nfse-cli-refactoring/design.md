# Documento de Design

## Visão Geral

Este documento descreve o design técnico para a refatoração do nfse-cli, uma ferramenta de linha de comando em Python para emissão de Nota Fiscal de Serviço Eletrônica (NFS-e) do Governo Federal. A refatoração visa corrigir problemas existentes, melhorar a estrutura do código, adicionar validações robustas, implementar testes automatizados e melhorar a experiência do usuário.

### Objetivos Principais

1. Corrigir inconsistências entre código e arquivos de exemplo
2. Implementar validações robustas de dados de entrada
3. Adicionar modo dry-run para simulação de operações
4. Criar comando de inicialização interativo
5. Padronizar nomes de arquivos e estrutura de diretórios
6. Implementar logging estruturado e completo
7. Adicionar testes automatizados (unitários e property-based)
8. Melhorar tratamento de erros e mensagens ao usuário
9. Separar responsabilidades no código para melhor manutenibilidade

### Tecnologias Utilizadas

- **Linguagem**: Python 3.7+
- **CLI Framework**: argparse (built-in)
- **XML**: lxml
- **Assinatura Digital**: signxml
- **Criptografia**: cryptography, pyOpenSSL
- **HTTP**: requests
- **Testes**: pytest, pytest-mock, hypothesis (property-based testing)

### Informações Oficiais da API

- **Ambiente de Produção Restrita**: https://adn.producaorestrita.nfse.gov.br
- **Ambiente de Produção**: https://adn.nfse.gov.br
- **Formato de Comunicação**: JSON
- **Formato do DPS**: XML comprimido com Gzip e codificado em Base64
- **Autenticação**: mTLS (mutual TLS) com certificado digital A1
- **Endpoints Principais**:
  - POST `/nfse` - Emissão síncrona de NFS-e
  - GET `/nfse/{chaveAcesso}` - Consulta de NFS-e
  - GET `/danfse/{chaveAcesso}` - Download do PDF (DANFSe)
  - GET `/dps/{id}` - Recupera chave de acesso da NFS-e a partir do ID do DPS
  - POST `/nfse/{chaveAcesso}/eventos` - Registro de eventos de NFS-e
- **Versão do Leiaute**: v1.01 (20260122)

## Arquitetura

### Estrutura de Módulos

O sistema será refatorado para seguir uma arquitetura modular com separação clara de responsabilidades:

```
nfse-cli/
├── nfse.py                 # Entry point CLI
├── nfse_core/              # Módulo principal
│   ├── __init__.py
│   ├── cli.py              # Parsing de argumentos e orquestração
│   ├── config.py           # Gerenciamento de configuração
│   ├── validation.py       # Validação de dados
│   ├── xml_builder.py      # Construção de XML DPS
│   ├── crypto.py           # Operações criptográficas
│   ├── api_client.py       # Comunicação com API
│   ├── file_manager.py     # Gerenciamento de arquivos
│   ├── logger.py           # Logging estruturado
│   └── models.py           # Modelos de dados
├── tests/                  # Testes automatizados
│   ├── __init__.py
│   ├── test_validation.py
│   ├── test_xml_builder.py
│   ├── test_crypto.py
│   ├── test_api_client.py
│   ├── test_file_manager.py
│   ├── test_integration.py
│   └── test_properties.py  # Property-based tests
├── cert/                   # Certificados digitais
├── logs/                   # Logs de operações
├── prestadores/            # JSONs de prestadores
├── tomadores/              # JSONs de tomadores
├── servicos/               # JSONs de serviços
├── danfse/                 # PDFs baixados
├── nfse/                   # XMLs de NFS-e emitidas
├── dps/                    # XMLs de DPS enviadas
├── config.json             # Configuração principal
├── requirements.txt        # Dependências de produção
└── requirements-dev.txt    # Dependências de desenvolvimento
```

### Fluxo de Dados

#### Comando `init`
```
Usuário executa `init`
    ↓
Criar diretórios
    ↓
Perguntar sobre dados da empresa
    ↓
Coletar dados interativamente
    ↓
Salvar prestador_{cnpj}.json
    ↓
Perguntar se define como padrão
    ↓
Atualizar config.json (se confirmado)
    ↓
Perguntar sobre dados do serviço
    ↓
Coletar dados interativamente
    ↓
Salvar servico_{codigo}.json
    ↓
Perguntar se define como padrão
    ↓
Atualizar config.json (se confirmado)
    ↓
Exibir resumo
```

#### Comando `emitir`
```
Usuário executa `emitir --valor X --data Y`
    ↓
Carregar config.json
    ↓
Validar certificado digital
    ↓
Carregar JSONs (prestador, tomador, serviço)
    ↓
Validar dados de entrada
    ↓
Gerar ID do DPS
    ↓
Construir XML do DPS
    ↓
Assinar XML com certificado
    ↓
Salvar DPS em dps/
    ↓
Comprimir (Gzip + Base64)
    ↓
[Se dry-run] Simular envio e parar
    ↓
[Se não dry-run] Enviar para API via mTLS
    ↓
Processar resposta
    ↓
Salvar NFS-e em nfse/
    ↓
Salvar log em logs/
    ↓
Exibir resultado
```

#### Comando `danfse`
```
Usuário executa `danfse <chave>`
    ↓
Carregar config.json
    ↓
Validar certificado digital
    ↓
Tentar consultar NFS-e (opcional)
    ↓
Se sucesso: Extrair CNPJ prestador e documento tomador
Se falha: Exibir aviso e continuar
    ↓
Fazer requisição GET mTLS para baixar PDF
    ↓
Salvar PDF em danfse/ com nome:
  - Completo: {timestamp}_{cnpj}_{doc}_{chave}.pdf
  - Simplificado: {timestamp}_{chave}.pdf
    ↓
Exibir resultado (sem log)
```

#### Comando `importar`
```
Usuário executa `importar <chave>`
    ↓
Carregar config.json
    ↓
Validar certificado digital
    ↓
Fazer requisição GET para obter NFS-e
    ↓
Parsear XML da NFS-e
    ↓
Extrair dados do prestador
    ↓
Salvar prestador_{timestamp}.json
    ↓
Extrair dados do tomador
    ↓
Salvar tomador_{timestamp}.json
    ↓
Extrair dados do serviço
    ↓
Salvar servico_{timestamp}.json
    ↓
Exibir caminhos dos arquivos criados
```

## Componentes e Interfaces

### 1. Módulo `cli.py`

Responsável pelo parsing de argumentos e orquestração dos comandos.

```python
def main():
    """Entry point principal da aplicação"""
    parser = criar_parser()
    args = parser.parse_args()
    
    # Configurar modo verbose/silent
    configurar_output(args)
    
    # Executar comando apropriado
    if args.command == 'init':
        executar_init(args)
    elif args.command == 'emitir':
        executar_emitir(args)
    elif args.command == 'danfse':
        executar_danfse(args)
    elif args.command == 'importar':
        executar_importar(args)
    else:
        parser.print_help()

def criar_parser() -> argparse.ArgumentParser:
    """Cria e configura o parser de argumentos"""
    # Argumentos globais: --verbose, --silent
    # Subcomandos: init, emitir, danfse, importar
    pass

def executar_init(args):
    """Executa o comando de inicialização"""
    pass

def executar_emitir(args):
    """Executa o comando de emissão de NFS-e"""
    pass

def executar_danfse(args):
    """Executa o comando de download de DANFSe"""
    pass

def executar_importar(args):
    """Executa o comando de importação de NFS-e"""
    pass
```

### 2. Módulo `config.py`

Gerencia a leitura e escrita do arquivo de configuração.

```python
@dataclass
class Config:
    """Configuração da aplicação"""
    ambiente: str  # 'producao' ou 'producaorestrita'
    dry_run: bool
    urls: Dict[str, str]
    arquivo_pfx: str
    arquivo_senha_cert: str
    serie: int
    proximo_numero: int
    defaults: Dict[str, str]
    
    @classmethod
    def carregar(cls, caminho: str = 'config.json') -> 'Config':
        """Carrega configuração do arquivo JSON"""
        pass
    
    def salvar(self, caminho: str = 'config.json'):
        """Salva configuração no arquivo JSON"""
        pass
    
    def atualizar_default(self, tipo: str, caminho: str):
        """Atualiza um caminho padrão (prestador ou servico)"""
        pass
    
    def obter_url_api(self, ambiente: Optional[str] = None) -> str:
        """Retorna URL da API para o ambiente especificado"""
        pass
```

### 3. Módulo `validation.py`

Contém todas as funções de validação de dados.

```python
class ValidationError(Exception):
    """Exceção para erros de validação"""
    pass

def validar_cnpj(cnpj: str) -> bool:
    """Valida formato de CNPJ (14 dígitos)"""
    pass

def validar_cpf(cpf: str) -> bool:
    """Valida formato de CPF (11 dígitos)"""
    pass

def validar_codigo_municipio(codigo: str) -> bool:
    """Valida código IBGE de município (7 dígitos)"""
    pass

def validar_codigo_tributacao(codigo: str) -> bool:
    """Valida formato de código de tributação nacional (6 dígitos numéricos)"""
    pass

def validar_valor(valor: float) -> bool:
    """Valida que o valor é positivo"""
    pass

def validar_data_iso(data: str) -> bool:
    """Valida formato de data ISO 8601"""
    pass

def validar_prestador(dados: Dict) -> List[str]:
    """Valida dados do prestador, retorna lista de erros"""
    pass

def validar_tomador(dados: Dict) -> List[str]:
    """Valida dados do tomador, retorna lista de erros"""
    pass

def validar_servico(dados: Dict) -> List[str]:
    """Valida dados do serviço, retorna lista de erros"""
    pass
```

### 4. Módulo `models.py`

Define os modelos de dados com validação.

```python
@dataclass
class Endereco:
    """Endereço do tomador"""
    xLgr: str  # Logradouro
    nro: str  # Número
    xBairro: str  # Bairro
    cMun: str  # Código município IBGE
    CEP: str  # CEP
    
    def validar(self) -> List[str]:
        """Valida os dados do endereço"""
        pass

@dataclass
class RegimeTributario:
    """Regime tributário do prestador"""
    opSimpNac: int  # Opção pelo Simples Nacional (1=Não Optante, 2=MEI, 3=ME/EPP)
    regEspTrib: int  # Regime Especial de Tributação (0=Nenhum, 1-6 ou 9=Outros)
    regApTribSN: Optional[int] = None  # Regime de apuração (1, 2 ou 3) - apenas se opSimpNac=3
    
    def validar(self) -> List[str]:
        """Valida os dados do regime tributário"""
        pass

@dataclass
class Prestador:
    """Dados do prestador de serviço"""
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    xNome: str = ""
    cMun: str = ""  # Código município
    IM: Optional[str] = None  # Inscrição municipal
    email: Optional[str] = None
    regTrib: RegimeTributario = None  # Regime tributário (obrigatório)
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Prestador':
        """Carrega prestador de arquivo JSON"""
        pass
    
    def salvar(self, caminho: str):
        """Salva prestador em arquivo JSON"""
        pass
    
    def validar(self) -> List[str]:
        """Valida os dados do prestador"""
        pass
    
    def obter_documento(self) -> str:
        """Retorna CNPJ ou CPF"""
        return self.CNPJ or self.CPF

@dataclass
class Tomador:
    """Dados do tomador de serviço"""
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    xNome: str = ""
    email: Optional[str] = None
    end: Optional[Endereco] = None
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Tomador':
        """Carrega tomador de arquivo JSON"""
        pass
    
    def salvar(self, caminho: str):
        """Salva tomador em arquivo JSON"""
        pass
    
    def validar(self) -> List[str]:
        """Valida os dados do tomador"""
        pass
    
    def obter_documento(self) -> str:
        """Retorna CNPJ ou CPF"""
        return self.CNPJ or self.CPF

@dataclass
class Servico:
    """Dados do serviço prestado"""
    xDescServ: str  # Descrição completa do serviço
    cTribNac: str  # Código tributação nacional (6 dígitos numéricos)
    cLocPrestacao: str  # Código município IBGE onde o serviço foi prestado
    cTribMun: Optional[str] = None  # Código tributação municipal (3 dígitos)
    cNBS: Optional[str] = None  # Código NBS
    cIntContrib: Optional[str] = None  # Código interno do contribuinte
    
    @classmethod
    def carregar(cls, caminho: str) -> 'Servico':
        """Carrega serviço de arquivo JSON"""
        pass
    
    def salvar(self, caminho: str):
        """Salva serviço em arquivo JSON"""
        pass
    
    def validar(self) -> List[str]:
        """Valida os dados do serviço"""
        pass
```

### 5. Módulo `xml_builder.py`

Constrói o XML do DPS seguindo o schema oficial.

```python
def gerar_id_dps(prestador: Prestador, config: Config) -> str:
    """
    Gera o ID do DPS conforme especificação:
    Formato: Mun(7) + TipoInsc(1) + Insc(14) + Serie(5) + Num(15)
    """
    pass

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
    
    Estrutura:
    <DPS versao="1.01">
      <infDPS Id="{id_dps}">
        <tpAmb>{config.ambiente}</tpAmb>
        <dhEmi>{data_emissao}</dhEmi>
        <verAplic>{config.versao_aplicativo}</verAplic>
        <serie>{config.serie}</serie>
        <nDPS>{config.proximo_numero}</nDPS>
        <dCompet>{data_competencia}</dCompet>
        <tpEmit>1</tpEmit>
        <cLocEmi>{prestador.cMun}</cLocEmi>
        <prest>
          <CNPJ>{prestador.CNPJ}</CNPJ>
          <IM>{prestador.IM}</IM>
          <xNome>{prestador.xNome}</xNome>
          <end>...</end>
          <email>{prestador.email}</email>
          <regTrib>
            <opSimpNac>{prestador.regTrib.opSimpNac}</opSimpNac>
            <regApTribSN>{prestador.regTrib.regApTribSN}</regApTribSN>
            <regEspTrib>{prestador.regTrib.regEspTrib}</regEspTrib>
          </regTrib>
        </prest>
        <toma>
          <CNPJ>{tomador.CNPJ}</CNPJ>
          <xNome>{tomador.xNome}</xNome>
          <email>{tomador.email}</email>
          <end>
            <endNac>
              <cMun>{tomador.end.cMun}</cMun>
              <CEP>{tomador.end.CEP}</CEP>
            </endNac>
            <xLgr>{tomador.end.xLgr}</xLgr>
            <nro>{tomador.end.nro}</nro>
            <xBairro>{tomador.end.xBairro}</xBairro>
          </end>
        </toma>
        <serv>
          <locPrest>
            <cLocPrestacao>{servico.cLocPrestacao}</cLocPrestacao>
          </locPrest>
          <cServ>
            <cTribNac>{servico.cTribNac}</cTribNac>
            <cTribMun>{servico.cTribMun}</cTribMun>
            <xDescServ>{servico.xDescServ}</xDescServ>
            <cNBS>{servico.cNBS}</cNBS>
          </cServ>
        </serv>
        <valores>
          <vServ>{valor}</vServ>
          ...
        </valores>
      </infDPS>
    </DPS>
    """
    pass

def xml_para_string(xml: etree.Element) -> str:
    """Converte elemento XML para string"""
    pass
```

### 6. Módulo `crypto.py`

Gerencia operações criptográficas e validação de certificados.

```python
@dataclass
class CertificadoInfo:
    """Informações do certificado"""
    titular: str
    emissor: str
    validade_inicio: datetime
    validade_fim: datetime
    dias_para_expirar: int
    eh_icp_brasil: bool

def carregar_pfx(arquivo_pfx: str, senha: str) -> bytes:
    """
    Carrega certificado PFX e retorna em formato PEM.
    Mantém em memória por segurança.
    """
    pass

def validar_certificado(arquivo_pfx: str, senha: str) -> CertificadoInfo:
    """
    Valida certificado digital:
    - Verifica validade
    - Verifica se é ICP-Brasil
    - Retorna informações do certificado
    """
    pass

def assinar_xml(xml: etree.Element, pem_data: bytes) -> etree.Element:
    """
    Assina XML com XMLDSig (enveloped signature).
    Usa algoritmo rsa-sha1 conforme especificação.
    """
    pass

def comprimir_xml(xml: etree.Element) -> str:
    """
    Comprime XML com Gzip e codifica em Base64.
    Retorna string base64.
    
    Processo:
    1. Converte XML para string
    2. Codifica string em bytes UTF-8
    3. Comprime com Gzip
    4. Codifica resultado em Base64
    
    Este é o formato esperado pela API oficial da Sefin Nacional.
    """
    pass

def descomprimir_xml(base64_data: str) -> str:
    """
    Decodifica Base64 e descomprime Gzip.
    Retorna string XML.
    
    Processo inverso de comprimir_xml:
    1. Decodifica Base64 para bytes
    2. Descomprime Gzip
    3. Decodifica bytes UTF-8 para string
    """
    pass
```

### 7. Módulo `api_client.py`

Gerencia comunicação com a API da NFS-e.

```python
@dataclass
class RespostaAPI:
    """Resposta da API"""
    sucesso: bool
    status_code: int
    dados: Dict
    erro: Optional[str] = None

class APIClient:
    """Cliente para comunicação com API NFS-e"""
    
    def __init__(self, config: Config, pem_data: bytes):
        self.config = config
        self.pem_data = pem_data
        self.temp_cert_file = None
    
    def __enter__(self):
        """Context manager para gerenciar arquivo temporário de certificado"""
        self.temp_cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
        self.temp_cert_file.write(self.pem_data)
        self.temp_cert_file.close()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpa arquivo temporário"""
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
        """
        pass
    
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
        """
        pass
    
    def baixar_danfse(self, chave_acesso: str) -> bytes:
        """
        Baixa PDF do DANFSe.
        
        Endpoint: GET /danfse/{chaveAcesso}
        
        Retorna: bytes do arquivo PDF
        """
        pass
```

### 8. Módulo `file_manager.py`

Gerencia criação de diretórios e salvamento de arquivos.

```python
class FileManager:
    """Gerenciador de arquivos e diretórios"""
    
    DIRETORIOS = ['cert', 'logs', 'prestadores', 'tomadores', 
                  'servicos', 'danfse', 'nfse', 'dps']
    
    @staticmethod
    def criar_diretorios():
        """Cria todos os diretórios necessários"""
        pass
    
    @staticmethod
    def gerar_nome_arquivo(
        timestamp: str,
        cnpj_prestador: str,
        documento_tomador: str,
        extensao: str
    ) -> str:
        """
        Gera nome padronizado de arquivo:
        {timestamp}_{cnpj_prestador}_{documento_tomador}.{extensao}
        """
        pass
    
    @staticmethod
    def gerar_timestamp() -> str:
        """Gera timestamp no formato YYYYMMDD_HHMMSS"""
        pass
    
    @staticmethod
    def salvar_dps(xml: str, nome_arquivo: str):
        """Salva XML do DPS no diretório dps/"""
        pass
    
    @staticmethod
    def salvar_nfse(xml: str, nome_arquivo: str):
        """Salva XML da NFS-e no diretório nfse/"""
        pass
    
    @staticmethod
    def salvar_danfse(pdf_bytes: bytes, nome_arquivo: str):
        """Salva PDF do DANFSe no diretório danfse/"""
        pass
    
    @staticmethod
    def salvar_log(dados: Dict, nome_arquivo: str):
        """Salva log JSON no diretório logs/"""
        pass
```

### 9. Módulo `logger.py`

Gerencia logging estruturado.

```python
@dataclass
class LogEmissao:
    """Estrutura de log para emissão de NFS-e"""
    timestamp: str
    ambiente: str
    dry_run: bool
    prestador: Dict
    tomador: Dict
    servico: Dict
    valor: float
    data_emissao: str
    id_dps: str
    resposta_api: Dict
    metadados: Dict
    
    def para_dict(self) -> Dict:
        """Converte para dicionário"""
        pass
    
    def salvar(self, caminho: str):
        """Salva log em arquivo JSON formatado"""
        pass

def criar_log_emissao(
    config: Config,
    prestador: Prestador,
    tomador: Tomador,
    servico: Servico,
    valor: float,
    data_emissao: str,
    id_dps: str,
    resposta: RespostaAPI
) -> LogEmissao:
    """Cria objeto de log estruturado"""
    pass

def obter_metadados() -> Dict:
    """Obtém metadados do sistema (versão Python, SO, etc)"""
    pass
```

## Modelos de Dados

### Estrutura de Arquivos JSON

#### prestador_{cnpj}.json
```json
{
  "CNPJ": "12345678000190",
  "xNome": "EMPRESA EXEMPLO LTDA",
  "cMun": "3550308",
  "IM": "12345678",
  "email": "contato@empresa.com.br",
  "regTrib": {
    "opSimpNac": 1,
    "regEspTrib": 0,
    "regApTribSN": null
  }
}
```

#### tomador_{documento}.json
```json
{
  "CNPJ": "98765432000100",
  "xNome": "CLIENTE EXEMPLO LTDA",
  "email": "financeiro@cliente.com.br",
  "end": {
    "xLgr": "Avenida Paulista",
    "nro": "1000",
    "xBairro": "Bela Vista",
    "cMun": "3550308",
    "CEP": "01310100"
  }
}
```

#### servico_{codigo}.json
```json
{
  "xDescServ": "SERVICOS DE CONSULTORIA EM TECNOLOGIA DA INFORMACAO",
  "cTribNac": "010101",
  "cLocPrestacao": "3550308",
  "cTribMun": "001",
  "cNBS": null
}
```

#### config.json
```json
{
  "ambiente": "producaorestrita",
  "dry_run": true,
  "urls": {
    "producao": "https://adn.nfse.gov.br",
    "producaorestrita": "https://adn.producaorestrita.nfse.gov.br"
  },
  "arquivo_pfx": "cert/certificado.pfx",
  "arquivo_senha_cert": "cert/certificado.secret",
  "serie": 1,
  "proximo_numero": 1,
  "versao_aplicativo": "nfse-cli-2.0.0",
  "defaults": {
    "prestador": "prestadores/prestador_12345678000190.json",
    "tomador": "tomadores/tomador_exemplo.json",
    "servicos": "servicos/servico_010101.json"
  }
}
```

#### Log de Emissão (logs/{timestamp}_{cnpj}_{doc}.json)
```json
{
  "timestamp": "20240115_143022",
  "ambiente": "producaorestrita",
  "dry_run": false,
  "prestador": {
    "CNPJ": "12345678000190",
    "xNome": "EMPRESA EXEMPLO LTDA",
    "cMun": "3550308",
    "cServ": "01.01"
  },
  "tomador": {
    "CNPJ": "98765432000100",
    "xNome": "CLIENTE EXEMPLO LTDA"
  },
  "servico": {
    "xDescServ": "SERVICOS DE CONSULTORIA",
    "cTribNac": "010101",
    "cLocPrestacao": "3550308"
  },
  "valor": 1500.00,
  "data_emissao": "2024-01-15T14:30:22-03:00",
  "id_dps": "35503082123456780001900001000000000000001",
  "resposta_api": {
    "tipoAmbiente": 2,
    "versaoAplicativo": "1.0.0",
    "dataHoraProcessamento": "2024-01-15T14:30:25-03:00",
    "chaveAcesso": "35503082123456780001900001000000000000001",
    "status_code": 201
  },
  "metadados": {
    "versao_python": "3.9.7",
    "sistema_operacional": "Linux",
    "versao_nfse_cli": "2.0.0"
  }
}
```


## Tratamento de Erros

### Hierarquia de Exceções

```python
class NFSeError(Exception):
    """Exceção base para erros do sistema"""
    pass

class ValidationError(NFSeError):
    """Erro de validação de dados"""
    pass

class CertificateError(NFSeError):
    """Erro relacionado a certificado digital"""
    pass

class APIError(NFSeError):
    """Erro na comunicação com API"""
    pass

class FileError(NFSeError):
    """Erro em operações de arquivo"""
    pass
```

### Validações Oficiais Obrigatórias

Com base nas regras de negócio oficiais (anexo_i-sefin_adn-dps_nfse-snnfse-v1-01-20260122_rn_dps.csv), o sistema deve implementar as seguintes validações:

#### Validações de Formato (Nível 1)

1. **CNPJ/CPF**: Validar formato e dígito verificador (DV)
   - CNPJ: 14 dígitos numéricos com DV válido
   - CPF: 11 dígitos numéricos com DV válido

2. **Código de Município (cMun)**: Exatamente 7 dígitos numéricos
   - Deve existir na tabela IBGE de municípios

3. **Código de Tributação Nacional (cTribNac)**: Exatamente 6 dígitos numéricos
   - Deve existir na lista nacional de serviços

4. **CEP**: 8 dígitos numéricos

#### Validações de Alíquotas (Nível 2)

1. **Alíquota Máxima**: Não pode ultrapassar 5%
   - Código de erro: E1300
   - Mensagem: "Não é permitido informar alíquota aplicada superior a 5%."

2. **Alíquota Mínima**: Não pode ser inferior a 2% (com exceções)
   - Código de erro: E1297
   - Exceções: Códigos de serviço específicos listados nas regras oficiais
   - Serviços com exceção à regra de 2%: 042201, 042301, 050901, 070201, 070202, 070501, 070502, 090201, 090202, 100101-100105, 100201-100202, 100301, 100401-100403, 100501-100502, 100601, 100701, 100801, 100901, 101001, 150101-150105, 151001-151005, 160101-160104, 160201, 170501, 170601, 171001-171002, 171101-171102, 171201, 210101, 250301

#### Validações de Incidência do ISSQN (Nível 2)

1. **Local de Incidência Obrigatório**: Quando tribISSQN = 1 (Operação Tributável)
   - Código de erro: E1305

2. **Local de Incidência Proibido**: Quando tribISSQN = 2, 3 ou 4 (Imunidade, Exportação, Não Incidência)
   - Código de erro: E1301

3. **Regras de Incidência por Código de Serviço**:
   - **Local da Prestação**: Códigos 030401-030403, 030501, 070201-070202, 070401, 070501-070502, 070901-070902, 071001-071002, 071101-071102, 071201, 071601, 071701, 071801, 071901, 110101-110102, 110201, 110301, 110401-110402, 120101-121701, 160101-160104, 160201, 171001-171002, 220101
     - cLocIncid deve ser igual a cLocPrestacao
     - Código de erro: E1317
   
   - **Domicílio do Tomador**: Código 170501
     - cLocIncid deve ser igual ao cMun do tomador
     - Código de erro: E1321
   
   - **Estabelecimento do Prestador**: Demais códigos não listados acima
     - cLocIncid deve ser igual ao cMun do prestador
     - Código de erro: E1325

#### Validações de Regime Tributário

1. **opSimpNac**: Valores válidos: 1 (Não Optante), 2 (MEI), 3 (ME/EPP)

2. **regEspTrib**: Valores válidos: 0 (Nenhum), 1-6 ou 9 (Outros regimes especiais)

3. **regApTribSN**: Opcional, apenas quando opSimpNac = 3
   - Valores válidos: 1, 2 ou 3

#### Validações de IBSCBS

1. **Obrigatoriedade**:
   - Opcional para optantes do Simples Nacional até 31/12/2026
   - Obrigatório para não optantes do Simples Nacional
   - Obrigatório para todos a partir de 01/01/2027

2. **Consistência**: Se informado na DPS, deve ser informado na NFS-e
   - Código de erro: E1515

### Estratégia de Tratamento

1. **Validação Antecipada**: Validar todos os dados antes de iniciar operações custosas
2. **Mensagens Claras**: Sempre informar o que deu errado e como corrigir
3. **Códigos de Saída**: Retornar códigos apropriados para automação
   - 0: Sucesso
   - 1: Erro de validação
   - 2: Erro de certificado
   - 3: Erro de API
   - 4: Erro de arquivo
4. **Logging de Erros**: Registrar erros em logs quando apropriado
5. **Stack Traces**: Mostrar apenas em modo verbose

### Exemplos de Mensagens de Erro

```
❌ Erro de Validação: Campo 'CNPJ' ausente no arquivo prestadores/prestador.json

❌ Erro de Validação: CNPJ '12345678000100' possui dígito verificador inválido

❌ Erro de Validação: Código de município '123' inválido. Deve ter exatamente 7 dígitos

❌ Erro de Validação: Código de tributação nacional '01.01' inválido. Deve ter exatamente 6 dígitos numéricos (ex: 010101)

❌ Erro de Validação: Alíquota de 6% ultrapassa o limite máximo de 5%

❌ Erro de Validação: Para o código de serviço 010101, o local de incidência deve ser o estabelecimento do prestador

❌ Erro de Certificado: Certificado expirado em 2023-12-31. Por favor, renove seu certificado digital.

❌ Erro de API (400): Dados inválidos - O código de município '123' não é válido. Deve ter 7 dígitos.

❌ Erro de Arquivo: Não foi possível ler o arquivo tomadores/cliente.json - Arquivo não encontrado
```

## Estratégia de Testes

### Abordagem Dual: Testes Unitários + Property-Based Testing

O sistema utilizará duas abordagens complementares de teste:

1. **Testes Unitários**: Para casos específicos, edge cases e exemplos concretos
2. **Property-Based Testing**: Para validar propriedades universais com dados gerados

### Framework de Property-Based Testing

Utilizaremos **Hypothesis** para Python, que:
- Gera automaticamente casos de teste
- Encontra edge cases que humanos não pensariam
- Executa mínimo 100 iterações por propriedade
- Fornece shrinking automático (simplifica casos de falha)

### Configuração de Testes

```python
# conftest.py
import pytest
from hypothesis import settings, Verbosity

# Configuração global do Hypothesis
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.load_profile("default")

@pytest.fixture
def config_exemplo():
    """Fixture com configuração de exemplo"""
    return Config(
        ambiente="producaorestrita",
        dry_run=True,
        urls={
            "producao": "https://sefin.nfse.gov.br/SefinNacional",
            "producaorestrita": "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional"
        },
        arquivo_pfx="cert/teste.pfx",
        arquivo_senha_cert="cert/teste.secret",
        serie=1,
        proximo_numero=1,
        defaults={}
    )

@pytest.fixture
def prestador_exemplo():
    """Fixture com prestador de exemplo"""
    return Prestador(
        CNPJ="12345678000190",
        xNome="EMPRESA TESTE LTDA",
        cMun="3550308",
        cServ="01.01"
    )

@pytest.fixture
def tomador_exemplo():
    """Fixture com tomador de exemplo"""
    return Tomador(
        CNPJ="98765432000100",
        xNome="CLIENTE TESTE LTDA",
        email="teste@cliente.com"
    )

@pytest.fixture
def servico_exemplo():
    """Fixture com serviço de exemplo"""
    return Servico(
        xDesc="SERVICOS DE TESTE",
        cTribNac="01.01.01"
    )
```

### Estratégias de Teste por Módulo

#### validation.py
- **Unitários**: Testar casos válidos e inválidos específicos
- **Properties**: Validar que funções de validação sempre retornam bool ou lista de erros

#### xml_builder.py
- **Unitários**: Testar construção de XML com dados conhecidos
- **Properties**: Validar que XML gerado sempre é válido segundo o schema

#### crypto.py
- **Unitários**: Testar assinatura e compressão com dados fixos
- **Properties**: Validar round-trip de compressão/descompressão

#### api_client.py
- **Unitários**: Testar com mocks de respostas da API
- **Properties**: Validar que dry-run nunca faz requisições reais

#### file_manager.py
- **Unitários**: Testar criação de diretórios e salvamento de arquivos
- **Properties**: Validar formato de nomes de arquivos

### Testes de Integração

Simular fluxo completo com mocks:
1. Carregar configuração
2. Validar dados
3. Construir XML
4. Assinar
5. Enviar (mockado)
6. Processar resposta
7. Salvar arquivos

### Testes de Dry-Run

Validar que modo dry-run:
- Executa todas as etapas até o envio
- Não faz requisições HTTP reais
- Salva DPS e logs corretamente
- Não salva NFS-e (pois não foi emitida)


## Propriedades de Correção

Uma propriedade é uma característica ou comportamento que deve ser verdadeiro em todas as execuções válidas de um sistema - essencialmente, uma declaração formal sobre o que o sistema deve fazer. Propriedades servem como a ponte entre especificações legíveis por humanos e garantias de correção verificáveis por máquina.

### Property 1: Padronização de Nomes de Arquivos

*Para qualquer* operação de emissão com prestador, tomador e timestamp válidos, todos os arquivos gerados (DPS, NFS-e, log) devem ter o mesmo nome base no formato `{timestamp}_{cnpj_prestador}_{documento_tomador}` e diferir apenas na extensão.

**Valida: Requisitos 3.1, 3.2**

### Property 2: Criação Automática de Diretórios

*Para qualquer* operação que precisa salvar um arquivo em um diretório inexistente, o sistema deve criar o diretório automaticamente antes de salvar o arquivo.

**Valida: Requisitos 2.1**

### Property 3: Mapeamento Bidirecional JSON-XML

*Para qualquer* conjunto de dados válidos de prestador, tomador e serviço, as chaves dos arquivos JSON devem corresponder exatamente às tags XML do DPS, e vice-versa (importar uma NFS-e deve gerar JSONs com as mesmas chaves).

**Valida: Requisitos 4.5, 9.7**

### Property 4: Valor CLI no XML

*Para qualquer* valor monetário positivo fornecido via CLI, o XML do DPS gerado deve conter esse valor exato na tag `<vServ>`.

**Valida: Requisitos 5.6**

### Property 5: Comportamento Dry-Run

*Para qualquer* operação de emissão em modo dry-run, o sistema deve: (1) executar todas as etapas de validação, construção de XML, assinatura e compressão, (2) salvar o arquivo DPS, (3) salvar o log, (4) NÃO fazer requisições HTTP reais, e (5) NÃO salvar arquivo de NFS-e.

**Valida: Requisitos 6.9, 6.12, 13.5**

### Property 6: Modo Silencioso

*Para qualquer* comando executado com o parâmetro `--silent`, o sistema não deve exibir mensagens informativas no stdout (apenas erros críticos no stderr).

**Valida: Requisitos 7.7**

### Property 7: Rejeição de Valores Inválidos

*Para qualquer* valor monetário menor ou igual a zero fornecido via CLI, o sistema deve rejeitar a operação com mensagem de erro antes de iniciar o processamento.

**Valida: Requisitos 10.3**

### Property 8: Validação de Documentos

*Para qualquer* string que não seja um CPF válido (11 dígitos) nem um CNPJ válido (14 dígitos), o sistema deve rejeitar a operação com mensagem de erro específica.

**Valida: Requisitos 10.4, 10.5**

### Property 9: Validação de Código de Tributação

*Para qualquer* string que não seja composta por exatamente 6 dígitos numéricos, o sistema deve rejeitar a operação quando usado como código de tributação nacional.

**Valida: Requisitos 10.7**

### Property 10: Código de Saída em Erros

*Para qualquer* operação que falha (validação, certificado, API, arquivo), o sistema deve retornar um código de saída diferente de zero.

**Valida: Requisitos 11.6**

### Property 11: DPS com Assinatura Digital

*Para qualquer* DPS gerado e salvo, o arquivo XML deve conter a tag `<ds:Signature>` indicando que foi assinado digitalmente.

**Valida: Requisitos 13.3**

### Property 12: Estrutura Completa de Log

*Para qualquer* operação de emissão, o log JSON salvo deve: (1) conter todas as chaves obrigatórias (timestamp, ambiente, dry_run, prestador, tomador, servico, valor, data_emissao, id_dps, resposta_api, metadados), (2) ser um JSON válido, e (3) estar formatado com indentação.

**Valida: Requisitos 15.1, 15.4**

### Property 13: Aceitação de Caminhos com Subdiretórios

*Para qualquer* caminho relativo válido (incluindo subdiretórios) fornecido via `--prestador`, `--tomador` ou `--servico`, o sistema deve aceitar e processar o arquivo corretamente.

**Valida: Requisitos 17.1**

### Property 14: Modo Verbose Exibe XML

*Para qualquer* operação executada com o parâmetro `--verbose`, o sistema deve exibir o XML gerado no stdout antes do envio.

**Valida: Requisitos 19.2**

### Property 15: Round-Trip de Compressão

*Para qualquer* XML válido, comprimir com Gzip+Base64 e depois descomprimir deve resultar no XML original equivalente.

**Valida: Requisitos técnicos de compressão/descompressão**

### Property 16: Formato de Nome de Arquivo de Prestador

*Para qualquer* CNPJ válido fornecido durante o comando `init`, o arquivo gerado deve ter o nome `prestador_{cnpj}.json` onde {cnpj} são os 14 dígitos.

**Valida: Requisitos 1.4**

### Property 17: Formato de Nome de Arquivo de Serviço

*Para qualquer* código de tributação nacional válido (6 dígitos numéricos) fornecido durante o comando `init`, o arquivo gerado deve ter o nome `servico_{codigo}.json` onde {codigo} são os 6 dígitos.

**Valida: Requisitos 1.9**

### Property 18: Validação de Regime Tributário

*Para qualquer* prestador válido, o campo `regTrib` deve ser obrigatório e conter `opSimpNac` (1, 2 ou 3) e `regEspTrib` (0-6 ou 9), e se `opSimpNac` for 3, então `regApTribSN` pode estar presente com valores 1, 2 ou 3.

**Valida: Requisitos 4.1, 4.9**

### Property 19: Campos Obrigatórios do DPS

*Para qualquer* DPS gerado, o XML deve conter todos os campos obrigatórios: `tpAmb`, `dhEmi`, `verAplic`, `serie`, `nDPS`, `dCompet`, `tpEmit`, e `cLocEmi`.

**Valida: Requisitos 4.8**

### Property 20: Estrutura do Serviço

*Para qualquer* serviço válido, deve conter os campos obrigatórios `xDescServ`, `cTribNac` (6 dígitos), e `cLocPrestacao` (7 dígitos), e o XML do DPS deve incluir a estrutura `locPrest` e `cServ` corretamente aninhadas.

**Valida: Requisitos 4.4**


## Estratégia de Testes Detalhada

### Abordagem Dual

O sistema utilizará duas abordagens complementares:

1. **Testes Unitários**: Para casos específicos, exemplos concretos e edge cases
2. **Property-Based Tests**: Para validar propriedades universais com dados gerados

### Configuração do Hypothesis

Cada property test deve:
- Executar mínimo 100 iterações
- Usar estratégias de geração apropriadas
- Incluir tag de referência ao design

```python
from hypothesis import given, strategies as st, settings

# Estratégias customizadas
@st.composite
def cnpj_valido(draw):
    """Gera CNPJ válido de 14 dígitos"""
    return draw(st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=14, max_size=14))

@st.composite
def cpf_valido(draw):
    """Gera CPF válido de 11 dígitos"""
    return draw(st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=11, max_size=11))

@st.composite
def codigo_tributacao_valido(draw):
    """Gera código de tributação com 6 dígitos numéricos"""
    return draw(st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=6, max_size=6)) draw(st.integers(min_value=10, max_value=99))
    d3 = draw(st.integers(min_value=10, max_value=99))
    return f"{d1}.{d2}.{d3}"

@st.composite
def valor_positivo(draw):
    """Gera valor monetário positivo"""
    return draw(st.floats(min_value=0.01, max_value=999999.99))
```

### Mapeamento de Properties para Testes

#### Property 1: Padronização de Nomes
```python
@given(
    cnpj=cnpj_valido(),
    documento_tomador=st.one_of(cnpj_valido(), cpf_valido()),
    timestamp=st.text(regex=r'\d{8}_\d{6}')
)
@settings(max_examples=100)
def test_property_1_padronizacao_nomes(cnpj, documento_tomador, timestamp):
    """
    Feature: nfse-cli-refactoring, Property 1: Padronização de Nomes de Arquivos
    
    Para qualquer operação de emissão, todos os arquivos gerados devem ter
    o mesmo nome base e diferir apenas na extensão.
    """
    nome_base = FileManager.gerar_nome_arquivo(timestamp, cnpj, documento_tomador, "")
    assert nome_base == f"{timestamp}_{cnpj}_{documento_tomador}"
    
    # Verificar que diferentes extensões mantêm o mesmo base
    nome_dps = FileManager.gerar_nome_arquivo(timestamp, cnpj, documento_tomador, "xml")
    nome_log = FileManager.gerar_nome_arquivo(timestamp, cnpj, documento_tomador, "json")
    
    assert nome_dps.startswith(nome_base)
    assert nome_log.startswith(nome_base)
    assert nome_dps.endswith(".xml")
    assert nome_log.endswith(".json")
```

#### Property 5: Comportamento Dry-Run
```python
@given(
    prestador=prestador_valido(),
    tomador=tomador_valido(),
    servico=servico_valido(),
    valor=valor_positivo()
)
@settings(max_examples=100)
def test_property_5_dry_run(prestador, tomador, servico, valor, tmp_path, mocker):
    """
    Feature: nfse-cli-refactoring, Property 5: Comportamento Dry-Run
    
    Para qualquer operação em modo dry-run, o sistema deve executar todas
    as etapas exceto o envio real e não deve salvar NFS-e.
    """
    # Mock da requisição HTTP para garantir que não é chamada
    mock_post = mocker.patch('requests.post')
    
    config = Config(ambiente="producaorestrita", dry_run=True, ...)
    
    # Executar emissão em dry-run
    resultado = executar_emitir(config, prestador, tomador, servico, valor)
    
    # Verificar que requisição HTTP NÃO foi feita
    mock_post.assert_not_called()
    
    # Verificar que DPS foi salvo
    assert (tmp_path / "dps").exists()
    assert len(list((tmp_path / "dps").glob("*.xml"))) == 1
    
    # Verificar que log foi salvo
    assert (tmp_path / "logs").exists()
    assert len(list((tmp_path / "logs").glob("*.json"))) == 1
    
    # Verificar que NFS-e NÃO foi salva
    assert not (tmp_path / "nfse").exists() or len(list((tmp_path / "nfse").glob("*.xml"))) == 0
```

#### Property 8: Validação de Documentos
```python
@given(documento_invalido=st.text().filter(lambda x: len(x) not in [11, 14] or not x.isdigit()))
@settings(max_examples=100)
def test_property_8_validacao_documentos(documento_invalido):
    """
    Feature: nfse-cli-refactoring, Property 8: Validação de Documentos
    
    Para qualquer string que não seja CPF ou CNPJ válido, o sistema deve
    rejeitar com mensagem de erro.
    """
    with pytest.raises(ValidationError) as exc_info:
        validar_documento(documento_invalido)
    
    assert "CPF" in str(exc_info.value) or "CNPJ" in str(exc_info.value)
```

#### Property 15: Round-Trip de Compressão
```python
@given(xml_content=st.text(min_size=10, max_size=10000))
@settings(max_examples=100)
def test_property_15_round_trip_compressao(xml_content):
    """
    Feature: nfse-cli-refactoring, Property 15: Round-Trip de Compressão
    
    Para qualquer XML, comprimir e descomprimir deve resultar no original.
    """
    # Criar elemento XML válido
    root = etree.Element("test")
    root.text = xml_content
    
    # Comprimir
    comprimido = comprimir_xml(root)
    assert isinstance(comprimido, str)
    
    # Descomprimir
    descomprimido = descomprimir_xml(comprimido)
    
    # Verificar equivalência
    root_recuperado = etree.fromstring(descomprimido)
    assert root_recuperado.text == xml_content
```

### Testes Unitários Específicos

#### Exemplos Concretos

```python
def test_init_cria_diretorios(tmp_path):
    """Testa que comando init cria todos os diretórios necessários"""
    os.chdir(tmp_path)
    executar_init(Args())
    
    for dir_name in FileManager.DIRETORIOS:
        assert (tmp_path / dir_name).exists()

def test_emitir_sem_valor_retorna_erro():
    """Testa que emitir sem --valor retorna erro"""
    with pytest.raises(SystemExit) as exc_info:
        main(['emitir'])
    
    assert exc_info.value.code != 0

def test_danfse_nao_gera_log(tmp_path, mocker):
    """Testa que comando danfse não gera arquivo de log"""
    mocker.patch('requests.get', return_value=MockResponse(200, b'PDF content'))
    
    os.chdir(tmp_path)
    executar_danfse(Args(chave='12345678901234567890123456789012345678901234567890'))
    
    # Verificar que PDF foi salvo
    assert (tmp_path / "danfse").exists()
    
    # Verificar que log NÃO foi criado
    assert not (tmp_path / "logs").exists() or len(list((tmp_path / "logs").glob("*.json"))) == 0

def test_certificado_nao_icp_brasil_retorna_erro():
    """Testa que certificado não ICP-Brasil é rejeitado"""
    with pytest.raises(CertificateError) as exc_info:
        validar_certificado("cert/nao_icp.pfx", "senha")
    
    assert "ICP-Brasil" in str(exc_info.value)

def test_verbose_tem_precedencia_sobre_silent(capsys):
    """Testa que --verbose tem precedência sobre --silent"""
    main(['emitir', '--valor', '100', '--verbose', '--silent', '--dry-run'])
    
    captured = capsys.readouterr()
    # Em modo verbose, deve haver output mesmo com --silent
    assert len(captured.out) > 0
```

### Testes de Integração

```python
def test_fluxo_completo_emissao_dry_run(tmp_path, mocker):
    """Testa fluxo completo de emissão em modo dry-run"""
    os.chdir(tmp_path)
    
    # Setup
    criar_config_teste(tmp_path)
    criar_arquivos_json_teste(tmp_path)
    
    # Mock de certificado
    mocker.patch('nfse_core.crypto.validar_certificado', return_value=CertificadoInfo(...))
    mocker.patch('nfse_core.crypto.carregar_pfx', return_value=b'PEM data')
    
    # Mock de requisição (não deve ser chamado)
    mock_post = mocker.patch('requests.post')
    
    # Executar
    resultado = main(['emitir', '--valor', '1500.00', '--dry-run'])
    
    # Verificações
    assert resultado == 0
    mock_post.assert_not_called()
    
    # Verificar arquivos criados
    assert len(list((tmp_path / "dps").glob("*.xml"))) == 1
    assert len(list((tmp_path / "logs").glob("*.json"))) == 1
    assert len(list((tmp_path / "nfse").glob("*.xml"))) == 0

def test_fluxo_completo_importar(tmp_path, mocker):
    """Testa fluxo completo de importação de NFS-e"""
    os.chdir(tmp_path)
    
    # Setup
    criar_config_teste(tmp_path)
    
    # Mock de resposta da API com XML de NFS-e
    xml_nfse = criar_xml_nfse_teste()
    mock_get = mocker.patch('requests.get', return_value=MockResponse(200, {
        'nfseXmlGZipB64': comprimir_xml(xml_nfse)
    }))
    
    # Executar
    resultado = main(['importar', '12345678901234567890123456789012345678901234567890'])
    
    # Verificações
    assert resultado == 0
    mock_get.assert_called_once()
    
    # Verificar arquivos criados
    assert len(list((tmp_path / "prestadores").glob("*.json"))) == 1
    assert len(list((tmp_path / "tomadores").glob("*.json"))) == 1
    assert len(list((tmp_path / "servicos").glob("*.json"))) == 1
```

### Cobertura de Testes

Objetivo: Mínimo 80% de cobertura de código

```bash
# Executar testes com cobertura
pytest --cov=nfse_core --cov-report=html --cov-report=term

# Executar apenas property tests
pytest -m property

# Executar apenas testes unitários
pytest -m unit

# Executar testes de integração
pytest -m integration
```

### Marcadores de Testes

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Testes unitários")
    config.addinivalue_line("markers", "property: Property-based tests")
    config.addinivalue_line("markers", "integration: Testes de integração")
    config.addinivalue_line("markers", "slow: Testes lentos")
```

