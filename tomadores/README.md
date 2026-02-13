# Diretório de Tomadores

Este diretório contém os arquivos JSON com dados dos **tomadores de serviço** (seus clientes).

## Arquivo de Exemplo

- `tomador.json.example` - Arquivo de exemplo com todos os campos e comentários explicativos

## Como Usar

1. **Copie o arquivo de exemplo:**
   ```bash
   copy tomador.json.example tomador_CNPJCLIENTE.json
   ```

2. **Edite com os dados do cliente:**
   - Substitua o CNPJ/CPF pelo documento do cliente
   - Atualize nome, email e endereço
   - O endereço é opcional mas recomendado

3. **Configure como padrão (opcional):**
   - Edite `config.json` e defina `defaults.tomador` com o caminho do arquivo
   - Útil se você emite notas sempre para o mesmo cliente

## Organização

Você pode criar subdiretórios para organizar seus clientes:

```
tomadores/
├── clientes_sp/
│   ├── tomador_98765432000100.json
│   └── tomador_11122233344.json
├── clientes_rj/
│   └── tomador_55566677788.json
└── tomador.json.example
```

## Campos Importantes

### Documento (obrigatório)
Use **CNPJ** OU **CPF**, nunca ambos:
- `"CNPJ": "98765432000100"` - 14 dígitos
- `"CPF": "12345678901"` - 11 dígitos

### Endereço (opcional, mas recomendado)
O endereço é usado para validar regras de incidência do ISSQN:

```json
"end": {
  "xLgr": "Avenida Paulista",
  "nro": "1000",
  "xBairro": "Bela Vista",
  "cMun": "3550308",  // Código IBGE do município
  "CEP": "01310100"   // CEP sem hífen
}
```

**Importante:** O código do município do tomador (`cMun`) é usado para validar a incidência do ISSQN em alguns casos (ex: código de serviço 170501).

## Correspondência com XML

As chaves do JSON correspondem às tags XML do DPS:

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

## Dicas

- Crie um arquivo para cada cliente
- Use nomes descritivos: `tomador_98765432000100.json` ou `tomador_empresa_xyz.json`
- Remova as chaves `_comentario*` se quiser arquivos mais limpos
- Valide o CNPJ/CPF antes de usar (o sistema valida o dígito verificador)
- Inclua o endereço sempre que possível para evitar problemas com regras de incidência
- O arquivo `.example` contém explicações detalhadas de TODOS os campos disponíveis
- Campos opcionais como telefone, complemento e endereço no exterior podem ser adicionados consultando o `.example`
- Use o comando `python nfse.py importar <chave_acesso>` para extrair dados de uma nota existente
