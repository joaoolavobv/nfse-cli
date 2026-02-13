# Diretório de Prestadores

Este diretório contém os arquivos JSON com dados dos **prestadores de serviço** (sua empresa).

## Arquivo de Exemplo

- `prestador.json.example` - Arquivo de exemplo com todos os campos e comentários explicativos

## Como Usar

1. **Copie o arquivo de exemplo:**
   ```bash
   copy prestador.json.example prestador_SEUCNPJ.json
   ```
   
   **Ou use o comando init interativo:**
   ```bash
   python nfse.py init
   ```
   O comando `init` coleta os dados do prestador interativamente e cria o arquivo automaticamente.

2. **Edite com seus dados:**
   - Substitua o CNPJ/CPF pelo seu documento
   - Atualize nome, município, inscrição municipal, etc.
   - Configure o regime tributário corretamente

3. **Configure como padrão (opcional):**
   - Edite `config.json` e defina `defaults.prestador` com o caminho do seu arquivo
   - Assim você não precisa usar `--prestador` toda vez

## Organização

Você pode criar subdiretórios para organizar múltiplos prestadores:

```
prestadores/
├── empresa_a/
│   └── prestador_12345678000190.json
├── empresa_b/
│   └── prestador_98765432000100.json
└── prestador.json.example
```

## Campos Importantes

### Documento (obrigatório)
Use **CNPJ** OU **CPF**, nunca ambos:
- `"CNPJ": "12345678000190"` - 14 dígitos
- `"CPF": "12345678901"` - 11 dígitos

### Regime Tributário (obrigatório)
O campo `regTrib` é **obrigatório** e define como você é tributado:

```json
"regTrib": {
  "opSimpNac": 1,     // 1=Não Optante, 2=MEI, 3=ME/EPP
  "regEspTrib": 0,    // 0=Nenhum, 1-6 ou 9=Outros
  "regApTribSN": null // Apenas se opSimpNac=3
}
```

**Importante:** O regime tributário afeta a obrigatoriedade do IBSCBS!
- Não optantes do Simples Nacional (opSimpNac=1) **devem** incluir IBSCBS no serviço
- Optantes (opSimpNac=2 ou 3) podem incluir IBSCBS opcionalmente até 2027

## Correspondência com XML

As chaves do JSON correspondem às tags XML do DPS:

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

## Dicas

- Mantenha um arquivo para cada prestador diferente
- Use nomes descritivos: `prestador_12345678000190.json`
- Remova as chaves `_comentario*` se quiser arquivos mais limpos
- Valide o CNPJ antes de usar (o sistema valida o dígito verificador)
- Use `python nfse.py init` para criar o arquivo interativamente com validações
- O arquivo `.example` contém explicações detalhadas de TODOS os campos disponíveis
- Campos opcionais como endereço completo, telefone e email podem ser adicionados consultando o `.example`
