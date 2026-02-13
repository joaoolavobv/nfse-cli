# 🚀 nfse-cli

Ferramenta de linha de comando (CLI) em Python para emissão e download de **Nota Fiscal de Serviço Eletrônica (NFS-e)** no padrão Nacional.

Esta ferramenta simplifica a integração com a API Sefin Nacional, permitindo a automação da emissão de notas fiscais diretamente do terminal.

---

## 📖 Guia Rápido

### 🎯 Início Rápido em 5 Passos

#### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

#### 2. Configure o sistema
```bash
python nfse.py init
```

Este comando irá:
- Criar todos os diretórios necessários
- Solicitar dados da empresa (prestador) interativamente
- Solicitar dados do serviço principal
- Criar arquivo `config.json` com valores padrão

#### 3. Configure o certificado digital
```bash
# Copie seu certificado .pfx para o diretório cert (criado pelo init)
# Exemplo: cert/certificado.pfx

# Crie um arquivo com a senha do certificado
echo "SUA_SENHA_AQUI" > cert/certificado.secret
```

#### 4. Crie um arquivo de tomador
```bash
# Copie o exemplo e edite com os dados do cliente
cp tomadores/tomador.json.example tomadores/tomador.json

# Edite o arquivo com os dados reais do cliente
# Mínimo necessário: CNPJ ou CPF, xNome, email
```

#### 5. Emita sua primeira nota (modo teste)
```bash
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --dry-run
```

### 💡 Comandos Principais

```bash
# Inicializar projeto
python nfse.py init

# Emitir nota fiscal (modo simulação)
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --dry-run

# Emitir nota fiscal com vírgula e data brasileira
python nfse.py emitir --valor 1500,00 --data 15/03/2026 --tomador tomadores/tomador.json --dry-run

# Emitir nota fiscal (envio real)
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --no-dry-run

# Baixar XML e PDF de uma nota existente
python nfse.py baixar <chave_acesso_50_digitos>
```

---

## 📖 Estrutura de Arquivos JSON

**As chaves dos arquivos JSON correspondem EXATAMENTE às tags XML oficiais do DPS.**

Isso garante consistência e facilita o entendimento da estrutura.

### Campos Principais por Arquivo

#### config.json

| Campo | Descrição | Tag XML |
|-------|-----------|---------|
| `arquivo_cert_pfx` | Caminho do certificado digital PFX | - |
| `arquivo_cert_senha` | Caminho do arquivo com senha do certificado | - |
| `serie` | Série do DPS (normalmente 1) | `<serie>` |
| `proximo_numero` | Número sequencial (auto-incrementado) | `<nDPS>` |
| `versao_aplicativo` | Versão do nfse-cli | `<verAplic>` |
| `defaults.ambiente` | "producao" ou "producaorestrita" | `<tpAmb>` |
| `defaults.dry_run` | true = simula, false = envia | - |
| `defaults.timeout` | Timeout em segundos para requisições HTTP | - |
| `defaults.prestador` | Caminho padrão do arquivo do prestador | - |
| `defaults.tomador` | Caminho padrão do arquivo do tomador | - |
| `defaults.servicos` | Caminho padrão do arquivo do serviço | - |

#### Prestador

| Campo | Descrição | Tag XML |
|-------|-----------|---------|
| `CNPJ` ou `CPF` | Documento (use apenas um) | `<CNPJ>` ou `<CPF>` |
| `xNome` | Nome/Razão social | `<xNome>` |
| `cMun` | Código município IBGE (7 dígitos) | `<cMun>` |
| `IM` | Inscrição Municipal (opcional) | `<IM>` |
| `regTrib` | Regime tributário (OBRIGATÓRIO) | `<regTrib>` |

**Regime Tributário:**
```json
"regTrib": {
  "opSimpNac": 1,     // 1=Não Optante, 2=MEI, 3=ME/EPP
  "regEspTrib": 0,    // 0=Nenhum, 1-6 ou 9=Outros
  "regApTribSN": null // Apenas se opSimpNac=3
}
```

#### Tomador

| Campo | Descrição | Tag XML |
|-------|-----------|---------|
| `CNPJ` ou `CPF` | Documento (use apenas um) | `<CNPJ>` ou `<CPF>` |
| `xNome` | Nome/Razão social | `<xNome>` |
| `email` | Email (opcional) | `<email>` |
| `end` | Endereço (opcional) | `<end>` |

**Endereço:**
```json
"end": {
  "xLgr": "Avenida Paulista",
  "nro": "1000",
  "xBairro": "Bela Vista",
  "cMun": "3550308",
  "CEP": "01310100"
}
```

#### Serviço

| Campo | Descrição | Tag XML |
|-------|-----------|---------|
| `xDescServ` | Descrição do serviço (pode ser sobrescrita via `--descricao` na linha de comando) | `<xDescServ>` |
| `cTribNac` | Código tributação (6 dígitos) | `<cTribNac>` |
| `cLocPrestacao` | Município da prestação | `<cLocPrestacao>` |
| `aliquota` | Alíquota ISSQN % (opcional) | - |
| `ibscbs` | Dados IBS/CBS (condicional) | `<IBSCBS>` |

**⚠️ NÃO inclua no serviço:**
- `vServ` (valor) - fornecido via `--valor`
- `dhEmi` (data) - fornecido via `--data`

### Exemplos de Correspondência JSON → XML

#### Prestador
```json
{
  "CNPJ": "12345678000190",
  "xNome": "EMPRESA EXEMPLO LTDA",
  "cMun": "3550308",
  "IM": "12345678"
}
```

Gera o XML:
```xml
<prest>
  <CNPJ>12345678000190</CNPJ>
  <xNome>EMPRESA EXEMPLO LTDA</xNome>
  <IM>12345678</IM>
</prest>
```

#### Tomador
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

Gera o XML:
```xml
<toma>
  <CNPJ>98765432000100</CNPJ>
  <xNome>CLIENTE EXEMPLO LTDA</xNome>
  <email>financeiro@cliente.com.br</email>
  <end>
    <endNac>
      <cMun>3550308</cMun>
      <CEP>01310100</CEP>
    </endNac>
    <xLgr>Avenida Paulista</xLgr>
    <nro>1000</nro>
    <xBairro>Bela Vista</xBairro>
  </end>
</toma>
```

#### Serviço
```json
{
  "xDescServ": "SERVICOS DE CONSULTORIA",
  "cTribNac": "010101",
  "cLocPrestacao": "3550308",
  "cTribMun": "001"
}
```

Gera o XML:
```xml
<serv>
  <locPrest>
    <cLocPrestacao>3550308</cLocPrestacao>
  </locPrest>
  <cServ>
    <cTribNac>010101</cTribNac>
    <cTribMun>001</cTribMun>
    <xDescServ>SERVICOS DE CONSULTORIA</xDescServ>
  </cServ>
</serv>
```

---

## 🎨 IBSCBS - IBS e CBS

### O que é IBSCBS?

O grupo IBSCBS contém informações sobre:
- **IBS**: Imposto sobre Bens e Serviços
- **CBS**: Contribuição sobre Bens e Serviços

### Quando é obrigatório?

#### Opcional
- Optantes do Simples Nacional (opSimpNac=2 ou 3)
- Antes de 01/01/2027

#### Obrigatório
- Não optantes do Simples Nacional (opSimpNac=1)
- Todos a partir de 01/01/2027

### Exemplo com IBSCBS

```json
{
  "xDescServ": "SERVICOS DE CONSULTORIA",
  "cTribNac": "010101",
  "cLocPrestacao": "3550308",
  "ibscbs": {
    "vIBS": 10.00,
    "vCBS": 5.00,
    "aliqIBS": 1.0,
    "aliqCBS": 0.5
  }
}
```

Gera o XML:
```xml
<valores>
  <vServ>1500.00</vServ>
  <IBSCBS>
    <vIBS>10.00</vIBS>
    <vCBS>5.00</vCBS>
    <aliqIBS>1.00</aliqIBS>
    <aliqCBS>0.50</aliqCBS>
  </IBSCBS>
</valores>
```

---

## ✅ Validações Automáticas

O sistema valida automaticamente:

### 1. Documentos
- **CNPJ**: 14 dígitos com validação de dígito verificador
- **CPF**: 11 dígitos com validação de dígito verificador

### 2. Alíquotas do ISSQN
- **Máximo**: 5%
- **Mínimo**: 2% (com exceções para códigos específicos)

Códigos com exceção à regra de 2%: 042201, 042301, 050901, 070201, 070202, 070501, 070502, 090201, 090202, 100101-100105, 100201-100202, 100301, 100401-100403, 100501-100502, 100601, 100701, 100801, 100901, 101001, 150101-150105, 151001-151005, 160101-160104, 160201, 170501, 170601, 171001-171002, 171101-171102, 171201, 210101, 250301

### 3. Regras de Incidência do ISSQN

O código de tributação nacional determina onde o ISSQN incide:

#### Incidência no domicílio do tomador
- **Código:** 170501
- O ISSQN é devido no município do cliente

#### Incidência no local da prestação
- **Códigos:** 030401-030403, 030501, 070201-070202, 070401, 070501-070502, 070901-070902, 071001-071002, 071101-071102, 071201, 071601, 071701, 071801, 071901, 110101-110102, 110201, 110301, 110401-110402, 120101-121701, 160101-160104, 160201, 171001-171002, 220101
- O ISSQN é devido no município onde o serviço foi prestado

#### Incidência no estabelecimento do prestador
- **Demais códigos**
- O ISSQN é devido no município da sua empresa

### 4. Obrigatoriedade do IBSCBS
- Baseado no regime tributário e data de competência
- Validação automática antes do envio

### 5. Formatos
- Códigos de município: 7 dígitos
- Códigos de tributação: 6 dígitos
- CEP: 8 dígitos
- Datas: ISO 8601

---

## ⚙️ Instalação e Configuração

### Pré-requisitos

- **Python 3.7+** instalado
- **Certificado Digital A1** (arquivo `.pfx` ou `.p12`) emitido pela ICP-Brasil
- Acesso à API Sefin Nacional (ambiente de produção ou produção restrita)

### Instalação

#### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/nfse-cli.git
cd nfse-cli
```

#### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

#### 3. Inicializar o projeto
```bash
python nfse.py init
```

### Configuração do Certificado Digital

#### Requisitos
- Certificado A1 no formato PFX/PKCS#12
- Emitido pela ICP-Brasil
- Dentro do prazo de validade
- Senha do certificado armazenada em arquivo separado

#### Passos
1. Coloque o arquivo `.pfx` no diretório `cert/`
2. Crie um arquivo `cert/certificado.secret` com a senha do certificado
3. Configure os caminhos no `config.json.example` e copie para `config.json`:
   ```json
   {
     "arquivo_cert_pfx": "cert/certificado.pfx",
     "arquivo_cert_senha": "cert/certificado.secret"
   }
   ```

---

## 🎛️ Opções Globais

Estas opções podem ser usadas com qualquer comando e devem vir ANTES do nome do comando:

### Controle de Ambiente

```bash
# Usar ambiente de produção
python nfse.py --producao <comando>

# Especificar ambiente explicitamente
python nfse.py --ambiente producao <comando>
python nfse.py --ambiente producaorestrita <comando>
```

**Observações:**
- `--producao` é um atalho para `--ambiente producao`
- Sobrescreve o ambiente configurado em `config.json`
- Padrão: usa o ambiente definido em `config.json` (defaults.ambiente)

### Controle de Verbosidade

```bash
# Modo verbose (exibe detalhes técnicos)
python nfse.py -v <comando>
python nfse.py --verbose <comando>

# Modo silencioso (apenas erros críticos)
python nfse.py -s <comando>
python nfse.py --silent <comando>
```

**Observações:**
- `--verbose` tem precedência sobre `--silent`
- Modo verbose exibe: XML gerado, payloads, URLs de requisição, headers HTTP
- Útil para debug e troubleshooting

### Controle de Timeout

```bash
# Definir timeout de 60 segundos
python nfse.py -t 60 <comando>
python nfse.py --timeout 60 <comando>
```

**Observações:**
- Sobrescreve o timeout configurado em `config.json` (defaults.timeout)
- Padrão: 30 segundos
- Útil quando a API está lenta ou há problemas de conexão
- Aplica-se a todas as requisições HTTP (emissão, consulta, download)

### Exemplos Combinados

```bash
# Baixar XML e PDF em produção com debug e timeout de 60s
python nfse.py --producao -v -t 60 baixar <chave_acesso>

# Emitir nota em produção restrita sem mensagens e timeout de 45s
python nfse.py --ambiente producaorestrita -s --timeout 45 emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json

# Emitir nota em produção com timeout customizado
python nfse.py --producao -t 90 emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json
```

---

## 📖 Uso Detalhado

### Comando: init

Inicializa a estrutura do projeto e cria arquivos de configuração:

```bash
python nfse.py init
```

Este comando irá:
- Criar todos os diretórios necessários
- Solicitar dados da empresa (prestador) interativamente
- Solicitar dados do serviço principal
- Criar arquivo `config.json` com valores padrão

### Comando: emitir

Emite uma NFS-e com os dados fornecidos.

**Parâmetros obrigatórios:**
- `--valor`: Valor monetário do serviço. Aceita vírgula ou ponto como separador decimal (ex: 1500.00 ou 1500,00)
- `--data`: Data/hora de emissão no formato YYYY-MM-DD (ex: 2026-03-15). Também aceita formato DD/MM/YYYY (ex: 15/03/2026)

**Parâmetros opcionais:**
- `--dry-run`: Ativa modo de simulação (não envia para API). Sobrescreve o valor do config.json
- `--no-dry-run`: Desativa modo de simulação (envia para API real). Sobrescreve o valor do config.json
- `--prestador`: Caminho do arquivo JSON do prestador
- `--tomador`: Caminho do arquivo JSON do tomador
- `--servico`: Caminho do arquivo JSON do serviço
- `--descricao`: Descrição do serviço (sobrescreve a descrição do arquivo JSON)

**Exemplos:**

```bash
# Emitir nota (formato YYYY-MM-DD)
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json

# Emitir nota (formato DD/MM/YYYY com vírgula)
python nfse.py emitir --valor 1500,00 --data 15/03/2026 --tomador tomadores/tomador.json

# Emitir em modo dry-run (simulação) - sobrescreve config.json
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --dry-run

# Forçar envio real mesmo se config.json tem defaults.dry_run: true
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --no-dry-run

# Usar tomador específico
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/cliente_especial.json

# Modo verbose (exibe detalhes técnicos)
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --verbose

# Usar arquivos em subdiretórios
python nfse.py emitir --valor 1500.00 --data 2026-03-15 \
  --prestador prestadores/empresa_a/prestador.json \
  --tomador tomadores/clientes_sp/cliente.json \
  --servico servicos/consultoria/servico.json

# Sobrescrever descrição do serviço
python nfse.py emitir --valor 1500.00 --data 2026-03-15 \
  --tomador tomadores/tomador.json \
  --descricao "Consultoria em TI - Projeto X - Sprint 3"

# Combinar descrição customizada com serviço específico
python nfse.py emitir --valor 2500.00 --data 2026-03-15 \
  --tomador tomadores/tomador.json \
  --servico servicos/consultoria/servico_010101.json \
  --descricao "Desenvolvimento de módulo de autenticação OAuth2"
```

**Sobre o parâmetro `--descricao`:**
- Sobrescreve o campo `xDescServ` do arquivo JSON do serviço
- Útil quando você tem um serviço padrão mas precisa especificar detalhes da nota
- Use aspas duplas para descrições com espaços
- Corresponde à tag XML `<xDescServ>`
- Máximo: 2000 caracteres

### Comando: baixar

Baixa o XML e o PDF (DANFSe) de uma NFS-e existente.

**Parâmetro obrigatório:**
- `chave_acesso`: Chave de acesso da NFS-e (50 dígitos)

**Comportamento:**
- Tenta baixar o XML da NFS-e e salva em `nfse/`
- Tenta baixar o PDF (DANFSe) e salva em `danfse/`
- Se um dos downloads falhar, ainda tenta baixar o outro
- Os arquivos são salvos com formato: `{timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.{extensao}`
- Se não conseguir extrair dados do prestador/tomador, usa formato simplificado: `{timestamp}_{chave_acesso}.{extensao}`
- NÃO cria arquivo de log

**Exemplos:**

```bash
# Baixar em ambiente de produção restrita (padrão)
python nfse.py baixar 35503082123456780001900001000000000000001234567890

# Baixar em ambiente de produção
python nfse.py --producao baixar 35503082123456780001900001000000000000001234567890

# Baixar com modo verbose (exibe detalhes)
python nfse.py -v baixar 35503082123456780001900001000000000000001234567890
```

---

## 🌐 Ambientes da API

### Produção Restrita (Testes)
- **URL**: `https://adn.producaorestrita.nfse.gov.br`
- Use este ambiente para testes e desenvolvimento
- Configuração padrão: `"defaults": { "ambiente": "producaorestrita" }`

### Produção
- **URL**: `https://adn.nfse.gov.br`
- Use apenas para emissões reais
- Configuração: `"defaults": { "ambiente": "producao" }`

### Modo Dry-Run
- Simula todas as operações sem enviar dados para a API
- Útil para validar dados e testar o fluxo
- Configuração padrão: `"defaults": { "dry_run": true }` no config.json
- Pode ser sobrescrito via linha de comando:
  - `--dry-run`: força modo simulação (mesmo se config.json tem false)
  - `--no-dry-run`: força envio real (mesmo se config.json tem true)
  - Sem parâmetro: usa o valor do config.json
- Salva DPS e logs normalmente
- NÃO salva NFS-e (pois não houve emissão real)

---

## 💡 Dicas e Boas Práticas

### 1. Sempre teste com dry-run primeiro
```bash
# Se config.json tem defaults.dry_run: false, force simulação
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --dry-run

# Se config.json tem defaults.dry_run: true, não precisa passar parâmetro
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json

# Para enviar de verdade quando config.json tem defaults.dry_run: true
python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json --no-dry-run
```

### 2. Use os arquivos .example como base
Copie e adapte os arquivos de exemplo:
```bash
cp prestadores/prestador.json.example prestadores/prestador.json
cp tomadores/tomador.json.example tomadores/tomador.json
cp servicos/servico.json.example servicos/servico.json
cp config.json.example config.json
```

### 3. Organize em subdiretórios
Para múltiplos prestadores/clientes:
```
prestadores/
├── empresa_a/
│   └── prestador.json
├── empresa_b/
│   └── prestador.json
```

### 4. Configure defaults no config.json
Copie `config.json.example` para `config.json` e configure defaults para evitar especificar parâmetros na linha de comando:
```json
{
  "defaults": {
    "ambiente": "producaorestrita",
    "dry_run": true,
    "timeout": 30,
    "prestador": "prestadores/prestador.json",
    "tomador": "tomadores/tomador_principal.json",
    "servicos": "servicos/servico.json"
  }
}
```

### 5. Remova comentários, se preferir
As chaves `_comentario*` podem ser removidas para arquivos mais limpos:
```bash
# Antes
{
  "_comentario": "Arquivo de configuração",
  "defaults": {
    "ambiente": "producaorestrita"
  },
  "_comentario_ambiente": "Ambiente da API"
}

# Depois
{
  "defaults": {
    "ambiente": "producaorestrita"
  }
}
```

### 6. Proteja arquivos sensíveis
- Nunca versione certificados ou senhas no git
- O `.gitignore` já está configurado para proteger:
  - Certificados (`.pfx`, `.p12`, `.pem`, `.key`)
  - Senhas (`.secret`)
  - Arquivos de configuração local (`config.json`)
  - XMLs e PDFs gerados (`*.xml`, `*.pdf`)
  - Logs (`*.json` em logs/)

**Importante:** Apenas os arquivos `.example` devem ser versionados no git.

---

## 🧪 Testes

O projeto utiliza **pytest** para testes unitários e **Hypothesis** para property-based testing.

### Instalar dependências de teste
```bash
pip install -r requirements-dev.txt
```

### Executar todos os testes
```bash
pytest
```

### Executar testes com cobertura
```bash
pytest --cov=nfse_core --cov-report=html --cov-report=term
```

### Executar testes específicos
```bash
# Apenas testes de modelos
pytest tests/test_models.py

# Modo verbose
pytest -v
```

### Estrutura de Testes
- ✅ 58 testes unitários
- ✅ Validação de Endereco, RegimeTributario, Prestador, Tomador, Servico
- ✅ Testes de carregamento/salvamento de arquivos JSON
- ✅ Testes de validação de campos obrigatórios e formatos
- ✅ Testes de logging estruturado e metadados do sistema
- ✅ Testes de integração com subdiretórios

---

## 🔧 Arquitetura

### Módulos Implementados

#### `models.py`
Define os modelos de dados com validação:
- `Endereco`: Endereço do tomador
- `RegimeTributario`: Regime tributário do prestador
- `Prestador`: Dados do prestador de serviço
- `Tomador`: Dados do tomador de serviço
- `Servico`: Dados do serviço prestado
- `IBSCBS`: Informações de IBS/CBS

#### `validation.py`
Funções de validação de dados:
- Validação de CNPJ e CPF (formato e dígito verificador)
- Validação de códigos de município (7 dígitos)
- Validação de códigos de tributação (6 dígitos)
- Validação de valores positivos
- Validação de datas ISO 8601
- Validação de alíquotas (máxima 5%, mínima 2% com exceções)
- Validação de regras de incidência do ISSQN
- Validação de obrigatoriedade do IBSCBS

#### `config.py`
Gerenciamento de configuração:
- Carregamento e salvamento de `config.json`
- Gerenciamento de ambientes (produção/producaorestrita)
- Configuração de modo dry-run
- Gerenciamento de defaults (prestador, tomador, serviço)

#### `file_manager.py`
Gerenciamento de arquivos:
- Criação automática de diretórios
- Geração de nomes padronizados de arquivos
- Salvamento de DPS, NFS-e, DANFSe e logs

#### `logger.py`
Logging estruturado:
- `LogEmissao`: Estrutura de log completa para operações de emissão
- `criar_log_emissao()`: Cria log estruturado a partir dos dados da operação
- `obter_metadados()`: Obtém metadados do sistema (versão Python, SO, etc)
- Salvamento automático de logs em JSON formatado

#### `crypto.py`
Criptografia e assinatura digital:
- Carregamento de certificados PFX
- Validação de certificados (validade, ICP-Brasil)
- Assinatura XML com XMLDSig
- Compressão e descompressão (Gzip + Base64)

#### `xml_builder.py`
Construção de XML:
- Geração de ID do DPS
- Construção completa do XML do DPS seguindo schema v1.01
- Inclusão de IBSCBS quando fornecido
- Conversão de XML para string

#### `api_client.py`
Comunicação com API:
- Cliente HTTP com autenticação mTLS
- Emissão de NFS-e
- Consulta de NFS-e
- Download de DANFSe
- Suporte a modo dry-run

#### `cli.py`
Interface de linha de comando:
- Parsing de argumentos
- Orquestração de comandos
- Tratamento de erros
- Modos verbose e silent

---

## 🐛 Troubleshooting

### Erro: "os seguintes argumentos são obrigatórios: --data", "--valor" ou "--tomador"
- Os parâmetros `--valor`, `--data` e `--tomador` são obrigatórios no comando `emitir`
- Exemplo correto: `python nfse.py emitir --valor 1500.00 --data 2026-03-15 --tomador tomadores/tomador.json`
- Use `python nfse.py emitir --help` para ver todos os parâmetros

### Erro: "Certificado expirado"
- Verifique a validade do seu certificado digital
- Renove o certificado se necessário
- O sistema exibe aviso se o certificado expira em menos de 30 dias

### Erro: "Certificado não é ICP-Brasil"
- Apenas certificados emitidos pela ICP-Brasil são aceitos
- Verifique a cadeia de certificação

### Erro: "Senha do certificado incorreta"
- Verifique o conteúdo do arquivo `.secret`
- Certifique-se de que não há espaços ou quebras de linha extras

### Erro: "CNPJ inválido"
- Verifique se o CNPJ tem 14 dígitos numéricos
- O sistema valida o dígito verificador automaticamente

### Erro: "Código de município inválido"
- Códigos de município devem ter exatamente 7 dígitos
- Use o código IBGE oficial do município

### Erro: "Data em formato inválido"
- A data deve estar no formato `YYYY-MM-DD` (ex: 2026-03-15) ou `DD/MM/YYYY` (ex: 15/03/2026)
- O sistema aceita ambos os formatos automaticamente

### Erro: "Alíquota ultrapassa 5%"
- A alíquota máxima do ISSQN é 5%
- Verifique o valor informado no arquivo JSON do serviço

### Erro: "Alíquota inferior a 2%"
- A alíquota mínima é 2% (com exceções para códigos específicos)
- Consulte a lista de códigos com exceção

### Erro: "Local de incidência incorreto"
- O sistema valida automaticamente as regras de incidência baseadas no código de serviço
- Verifique se o `cLocPrestacao` está correto
- Consulte as regras de incidência na seção de validações

### Erro: "IBSCBS obrigatório"
- IBSCBS é obrigatório para não optantes do Simples Nacional
- IBSCBS é obrigatório para todos a partir de 01/01/2027
- Adicione o grupo IBSCBS no arquivo JSON do serviço

### Testes falhando
- Instale as dependências de teste: `pip install -r requirements-dev.txt`
- Execute `pytest -v` para ver detalhes dos erros

---

## 🛡️ Segurança

**Nunca compartilhe arquivos sensíveis:**
- Certificados digitais (`.pfx`, `.p12`, `.pem`, `.key`)
- Senhas de certificados (`.secret`)
- Arquivo de configuração local (`config.json`)
- XMLs e PDFs gerados (podem conter dados sensíveis)
- Logs (podem conter dados sensíveis)

O `.gitignore` já está configurado para proteger esses arquivos. Apenas os arquivos `.example` devem ser versionados.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Implemente suas alterações e adicione testes
4. Execute os testes: `pytest`
5. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
6. Push para a branch (`git push origin feature/nova-funcionalidade`)
7. Abra um Pull Request

### Diretrizes
- Mantenha a cobertura de testes acima de 80%
- Siga as convenções de código Python (PEP 8)
- Adicione testes para novas funcionalidades
- Atualize a documentação quando necessário
- Use type hints quando possível

---

## 📚 Referências

- [API Sefin Nacional - Documentação Oficial](https://www.gov.br/nfse)
- Manual do Contribuinte (consulte documentação oficial)
- Schema DPS v1.01 (consulte documentação oficial)

---

## 📜 Licença

Este projeto está licenciado sob a licença **MIT** - veja o arquivo `LICENSE` para mais detalhes.

---

## 🆘 Suporte

Para dúvidas e problemas:
1. Consulte os guias detalhados dos diretórios:
   - [Prestadores - Guia Completo](prestadores/README.md)
   - [Tomadores - Guia Completo](tomadores/README.md)
   - [Serviços - Guia Completo](servicos/README.md)
2. Verifique os arquivos de exemplo (`.example`)
3. Leia os comentários inline nos arquivos JSON
4. Abra uma issue no GitHub

---

**Desenvolvido com ❤️ para facilitar a emissão de NFS-e no Brasil**
