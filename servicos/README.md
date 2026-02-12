# Diretório de Serviços

Este diretório contém os arquivos JSON com dados dos **serviços prestados**.

## Arquivos de Exemplo

- `servico.json.example` - Serviço básico sem IBSCBS
- `servico_com_ibscbs.json.example` - Serviço com informações de IBS/CBS

## Como Usar

1. **Escolha o exemplo apropriado:**
   - Use `servico.json.example` se você é optante do Simples Nacional e está antes de 2027
   - Use `servico_com_ibscbs.json.example` se você é não optante ou após 01/01/2027

2. **Copie o arquivo:**
   ```bash
   copy servico.json.example servico_010101.json
   ```

3. **Edite com os dados do serviço:**
   - Atualize a descrição do serviço
   - Configure o código de tributação nacional (6 dígitos, sem pontos)
   - Defina o local de prestação
   - Adicione IBSCBS se necessário

4. **Configure como padrão (opcional):**
   - Edite `config.json` e defina `defaults.servicos` com o caminho do arquivo

## Campos Importantes

### Código de Tributação Nacional (obrigatório)
```json
"cTribNac": "010101"  // 6 dígitos numéricos, SEM pontos
```

**Importante:** O código de tributação define as regras de incidência do ISSQN!

### Local de Prestação (obrigatório)
```json
"cLocPrestacao": "3550308"  // Código IBGE do município onde o serviço foi prestado
```

### Alíquota (opcional)
```json
"aliquota": 5.0  // Percentual (ex: 5.0 para 5%)
```

**Validações automáticas:**
- Máximo: 5%
- Mínimo: 2% (com exceções para códigos específicos)

### IBSCBS (condicional)

**Quando é obrigatório:**
- Você é **não optante** do Simples Nacional (opSimpNac=1 no prestador)
- A partir de **01/01/2027** para todos

**Quando é opcional:**
- Você é optante do Simples Nacional (opSimpNac=2 ou 3) antes de 2027

**Exemplo:**
```json
"ibscbs": {
  "vIBS": 10.00,      // Valor do IBS
  "vCBS": 5.00,       // Valor da CBS
  "aliqIBS": 1.0,     // Alíquota do IBS (opcional)
  "aliqCBS": 0.5      // Alíquota da CBS (opcional)
}
```

## O que NÃO incluir

**NUNCA inclua estes campos no arquivo JSON do serviço:**
- `vServ` (valor do serviço) - fornecido via `--valor` na linha de comando
- `dhEmi` (data de emissão) - fornecido via `--data` na linha de comando

Estes campos são fornecidos no momento da emissão porque variam a cada nota.

## Regras de Incidência do ISSQN

O código de tributação nacional determina onde o ISSQN incide:

### 1. Incidência no domicílio do tomador
- **Código:** 170501
- O ISSQN é devido no município do cliente

### 2. Incidência no local da prestação
- **Códigos:** 030401-030403, 030501, 070201-070202, 070401, 070501-070502, 070901-070902, 071001-071002, 071101-071102, 071201, 071601, 071701, 071801, 071901, 110101-110102, 110201, 110301, 110401-110402, 120101-121701, 160101-160104, 160201, 171001-171002, 220101
- O ISSQN é devido no município onde o serviço foi prestado

### 3. Incidência no estabelecimento do prestador
- **Demais códigos**
- O ISSQN é devido no município da sua empresa

O sistema valida automaticamente estas regras!

## Organização

Você pode criar subdiretórios para organizar diferentes tipos de serviço:

```
servicos/
├── consultoria/
│   ├── servico_010101.json
│   └── servico_010102.json
├── desenvolvimento/
│   └── servico_010201.json
└── servico.json.example
```

## Correspondência com XML

As chaves do JSON correspondem às tags XML do DPS:

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

Com IBSCBS:

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

## Dicas

- Crie um arquivo para cada tipo de serviço que você presta
- Use nomes descritivos: `servico_010101.json` ou `servico_consultoria.json`
- Remova as chaves `_comentario*` se quiser arquivos mais limpos
- Consulte a lista oficial de códigos de tributação em `nfse_docs/`
- Teste sempre com `--dry-run` antes de emitir de verdade
