# Plano de Implementação: Refatoração do nfse-cli

## Visão Geral

Este plano detalha a implementação da refatoração do nfse-cli, uma ferramenta de linha de comando em Python para emissão de Nota Fiscal de Serviço Eletrônica (NFS-e) do Governo Federal. A implementação seguirá uma abordagem modular, priorizando correções de bugs, validações robustas e testes automatizados.

### Abordagem de Implementação

1. Criar estrutura modular com separação clara de responsabilidades
2. Implementar validações robustas antes de operações custosas
3. Adicionar testes property-based e unitários incrementalmente
4. Implementar comandos em ordem de dependência (init → emitir → danfse → importar)
5. Garantir que cada etapa seja testável e validável

### Linguagem de Implementação

Python 3.7+

## Tarefas

- [x] 1. Configurar estrutura do projeto e dependências
  - Criar estrutura de diretórios do módulo `nfse_core/`
  - Criar arquivos `__init__.py` em todos os módulos
  - Criar `requirements.txt` com dependências de produção (lxml, signxml, cryptography, pyOpenSSL, requests)
  - Criar `requirements-dev.txt` com dependências de desenvolvimento (pytest, pytest-mock, pytest-cov, hypothesis)
  - Criar `conftest.py` com configuração do pytest e fixtures básicas
  - _Requisitos: 16.10_


- [x] 2. Implementar módulo de modelos de dados (models.py)
  - [x] 2.1 Criar dataclass `Endereco` com validação
    - Implementar campos: xLgr, nro, xBairro, cMun, CEP
    - Implementar método `validar()` que retorna lista de erros
    - _Requisitos: 4.3_
  
  - [x] 2.2 Criar dataclass `RegimeTributario` com validação
    - Implementar campos: opSimpNac, regEspTrib, regApTribSN (opcional)
    - Implementar método `validar()` que verifica valores válidos
    - Validar que regApTribSN só é permitido quando opSimpNac=3
    - _Requisitos: 4.9_
  
  - [x] 2.3 Criar dataclass `Prestador` com validação
    - Implementar campos: CNPJ/CPF, xNome, cMun, IM, email, regTrib
    - Implementar métodos: `carregar()`, `salvar()`, `validar()`, `obter_documento()`
    - Garantir que regTrib é obrigatório
    - _Requisitos: 4.1_
  
  - [x] 2.4 Criar dataclass `Tomador` com validação
    - Implementar campos: CNPJ/CPF, xNome, email, end
    - Implementar métodos: `carregar()`, `salvar()`, `validar()`, `obter_documento()`
    - _Requisitos: 4.2_
  
  - [x] 2.5 Criar dataclass `Servico` com validação
    - Implementar campos: xDescServ, cTribNac, cLocPrestacao, cTribMun, cNBS, cIntContrib
    - Implementar métodos: `carregar()`, `salvar()`, `validar()`
    - Garantir que NÃO contém campos vServ ou dhEmi
    - _Requisitos: 4.4, 4.7_
  
  - [ ]* 2.6 Escrever testes unitários para modelos
    - Testar carregamento e salvamento de JSON
    - Testar validação de campos obrigatórios
    - Testar casos de erro (campos ausentes, valores inválidos)
    - _Requisitos: 16.1_

- [x] 3. Implementar módulo de validação (validation.py)
  - [x] 3.1 Criar classe `ValidationError` para exceções de validação
    - _Requisitos: 11.1_
  
  - [x] 3.2 Implementar função `validar_cnpj()`
    - Validar formato de 14 dígitos numéricos
    - Validar dígito verificador (DV)
    - _Requisitos: 10.4_
  
  - [x] 3.3 Implementar função `validar_cpf()`
    - Validar formato de 11 dígitos numéricos
    - Validar dígito verificador (DV)
    - _Requisitos: 10.5_
  
  - [x] 3.4 Implementar função `validar_codigo_municipio()`
    - Validar formato de 7 dígitos numéricos
    - _Requisitos: 10.7_
  
  - [x] 3.5 Implementar função `validar_codigo_tributacao()`
    - Validar formato de 6 dígitos numéricos
    - _Requisitos: 10.8_
  
  - [x] 3.6 Implementar função `validar_valor()`
    - Validar que valor é positivo (> 0)
    - _Requisitos: 10.3_
  
  - [x] 3.7 Implementar função `validar_data_iso()`
    - Validar formato ISO 8601
    - _Requisitos: 5.3_
  
  - [x] 3.8 Implementar funções de validação de alíquotas
    - Implementar `validar_aliquota_maxima()` (não ultrapassar 5%)
    - Implementar `validar_aliquota_minima()` (não inferior a 2%, com exceções)
    - Implementar lista de códigos de serviço com exceção à regra de 2%
    - _Requisitos: 22.1, 22.2, 22.3_
  
  - [x] 3.9 Implementar validação de regras de incidência do ISSQN
    - Implementar `validar_local_incidencia()` que verifica regras por código de serviço
    - Validar incidência no local da prestação (códigos específicos)
    - Validar incidência no estabelecimento do prestador (códigos padrão)
    - Validar incidência no domicílio do tomador (código 170501)
    - _Requisitos: 24.1, 24.2, 24.3_
  
  - [ ]* 3.10 Escrever testes property-based para validações
    - **Property 7: Rejeição de Valores Inválidos**
    - **Valida: Requisitos 10.3**
  
  - [ ]* 3.11 Escrever testes property-based para validação de documentos
    - **Property 8: Validação de Documentos**
    - **Valida: Requisitos 10.4, 10.5**
  
  - [ ]* 3.12 Escrever testes property-based para código de tributação
    - **Property 9: Validação de Código de Tributação**
    - **Valida: Requisitos 10.7**
  
  - [ ]* 3.13 Escrever testes unitários para validações
    - Testar casos válidos e inválidos específicos
    - Testar mensagens de erro apropriadas
    - _Requisitos: 16.1_


- [x] 4. Implementar módulo de gerenciamento de arquivos (file_manager.py)
  - [x] 4.1 Criar classe `FileManager` com métodos estáticos
    - Definir constante `DIRETORIOS` com lista de diretórios necessários
    - _Requisitos: 1.1_
  
  - [x] 4.2 Implementar método `criar_diretorios()`
    - Criar todos os diretórios necessários se não existirem
    - Exibir mensagens informativas (exceto em modo silencioso)
    - _Requisitos: 1.1, 2.1, 2.3_
  
  - [x] 4.3 Implementar método `gerar_timestamp()`
    - Gerar timestamp no formato YYYYMMDD_HHMMSS
    - _Requisitos: 3.1_
  
  - [x] 4.4 Implementar método `gerar_nome_arquivo()`
    - Gerar nome padronizado: {timestamp}_{cnpj_prestador}_{documento_tomador}.{extensao}
    - _Requisitos: 3.1, 3.2_
  
  - [x] 4.5 Implementar métodos de salvamento de arquivos
    - Implementar `salvar_dps()` para salvar XML no diretório dps/
    - Implementar `salvar_nfse()` para salvar XML no diretório nfse/
    - Implementar `salvar_danfse()` para salvar PDF no diretório danfse/
    - Implementar `salvar_log()` para salvar JSON no diretório logs/
    - Todos os métodos devem criar diretórios automaticamente se necessário
    - _Requisitos: 3.4, 3.5, 3.6, 13.1, 13.2_
  
  - [ ]* 4.6 Escrever testes property-based para nomes de arquivos
    - **Property 1: Padronização de Nomes de Arquivos**
    - **Valida: Requisitos 3.1, 3.2**
  
  - [ ]* 4.7 Escrever testes property-based para criação de diretórios
    - **Property 2: Criação Automática de Diretórios**
    - **Valida: Requisitos 2.1**
  
  - [ ]* 4.8 Escrever testes unitários para file_manager
    - Testar criação de diretórios
    - Testar geração de nomes de arquivos
    - Testar salvamento de arquivos
    - _Requisitos: 16.3_

- [x] 5. Implementar módulo de configuração (config.py)
  - [x] 5.1 Criar dataclass `Config` com todos os campos
    - Implementar campos: ambiente, dry_run, urls, arquivo_pfx, arquivo_senha_cert, serie, proximo_numero, defaults
    - _Requisitos: 6.1, 6.2_
  
  - [x] 5.2 Implementar método `Config.carregar()`
    - Carregar configuração de config.json
    - Usar valores padrão se arquivo não existir
    - _Requisitos: 1.12_
  
  - [x] 5.3 Implementar método `Config.salvar()`
    - Salvar configuração em config.json formatado
    - _Requisitos: 1.12_
  
  - [x] 5.4 Implementar método `Config.atualizar_default()`
    - Atualizar chaves defaults.prestador ou defaults.servicos
    - _Requisitos: 1.6, 1.11_
  
  - [x] 5.5 Implementar método `Config.obter_url_api()`
    - Retornar URL correta baseada no ambiente
    - Suportar override via parâmetro
    - _Requisitos: 6.4, 6.5, 21.1, 21.2_
  
  - [ ]* 5.6 Escrever testes unitários para config
    - Testar carregamento e salvamento
    - Testar atualização de defaults
    - Testar obtenção de URL por ambiente
    - _Requisitos: 16.1_

- [x] 6. Checkpoint - Validar estrutura base
  - Garantir que todos os testes passam até aqui
  - Verificar que estrutura de módulos está correta
  - Perguntar ao usuário se há dúvidas ou ajustes necessários


- [x] 7. Implementar módulo de criptografia (crypto.py)
  - [x] 7.1 Criar dataclass `CertificadoInfo`
    - Implementar campos: titular, emissor, validade_inicio, validade_fim, dias_para_expirar, eh_icp_brasil
    - _Requisitos: 18.6_
  
  - [x] 7.2 Implementar função `carregar_pfx()`
    - Carregar certificado PFX e retornar em formato PEM
    - Manter em memória por segurança
    - Capturar exceção de senha incorreta
    - _Requisitos: 10.9, 10.10, 18.7_
  
  - [x] 7.3 Implementar função `validar_certificado()`
    - Verificar se certificado está dentro do prazo de validade
    - Verificar se é emitido pela ICP-Brasil (cadeia de certificação)
    - Exibir aviso se certificado expira em menos de 30 dias
    - Retornar `CertificadoInfo` com informações do certificado
    - _Requisitos: 18.1, 18.2, 18.3, 18.4, 18.5_
  
  - [x] 7.4 Implementar função `assinar_xml()`
    - Assinar XML com XMLDSig (enveloped signature)
    - Usar algoritmo rsa-sha1 conforme especificação
    - _Requisitos: 20.1_
  
  - [x] 7.5 Implementar função `comprimir_xml()`
    - Converter XML para string
    - Comprimir com Gzip
    - Codificar em Base64
    - Exibir tamanhos em modo verbose
    - _Requisitos: 20.2, 20.3, 20.5_
  
  - [x] 7.6 Implementar função `descomprimir_xml()`
    - Decodificar Base64
    - Descomprimir Gzip
    - Retornar string XML
    - _Requisitos: 20.2, 20.3_
  
  - [ ]* 7.7 Escrever testes property-based para round-trip de compressão
    - **Property 15: Round-Trip de Compressão**
    - **Valida: Requisitos técnicos de compressão/descompressão**
  
  - [ ]* 7.8 Escrever testes unitários para crypto
    - Testar assinatura de XML
    - Testar compressão e descompressão
    - Testar validação de certificado (com mocks)
    - _Requisitos: 16.2_

- [x] 8. Implementar módulo de construção de XML (xml_builder.py)
  - [x] 8.1 Implementar função `gerar_id_dps()`
    - Gerar ID no formato: Mun(7) + TipoInsc(1) + Insc(14) + Serie(5) + Num(15)
    - _Requisitos: 4.8_
  
  - [x] 8.2 Implementar função `construir_xml_dps()`
    - Construir estrutura completa do DPS seguindo schema v1.01
    - Incluir todos os campos obrigatórios: tpAmb, dhEmi, verAplic, serie, nDPS, dCompet, tpEmit, cLocEmi
    - Incluir estrutura completa de prestador com regTrib
    - Incluir estrutura completa de tomador com endereço
    - Incluir estrutura completa de serviço com locPrest e cServ
    - Incluir valores do serviço
    - Usar valor e data fornecidos via CLI (não de arquivos JSON)
    - _Requisitos: 4.5, 4.8, 4.9, 5.6_
  
  - [x] 8.3 Implementar função `xml_para_string()`
    - Converter elemento XML para string formatada
    - _Requisitos: técnicos_
  
  - [ ]* 8.4 Escrever testes property-based para mapeamento JSON-XML
    - **Property 3: Mapeamento Bidirecional JSON-XML**
    - **Valida: Requisitos 4.5, 9.7**
  
  - [ ]* 8.5 Escrever testes property-based para valor CLI no XML
    - **Property 4: Valor CLI no XML**
    - **Valida: Requisitos 5.6**
  
  - [ ]* 8.6 Escrever testes property-based para campos obrigatórios do DPS
    - **Property 19: Campos Obrigatórios do DPS**
    - **Valida: Requisitos 4.8**
  
  - [ ]* 8.7 Escrever testes property-based para estrutura do serviço
    - **Property 20: Estrutura do Serviço**
    - **Valida: Requisitos 4.4**
  
  - [ ]* 8.8 Escrever testes unitários para xml_builder
    - Testar construção de XML com dados conhecidos
    - Testar geração de ID do DPS
    - Verificar estrutura XML gerada
    - _Requisitos: 16.2_


- [x] 9. Implementar módulo de cliente da API (api_client.py)
  - [x] 9.1 Criar dataclass `RespostaAPI`
    - Implementar campos: sucesso, status_code, dados, erro
    - _Requisitos: técnicos_
  
  - [x] 9.2 Criar classe `APIClient` com context manager
    - Implementar `__init__()` que recebe config e pem_data
    - Implementar `__enter__()` que cria arquivo temporário de certificado
    - Implementar `__exit__()` que limpa arquivo temporário
    - _Requisitos: técnicos_
  
  - [x] 9.3 Implementar método `APIClient.emitir_nfse()`
    - Fazer POST para endpoint /nfse com payload JSON contendo DPS comprimido
    - Usar autenticação mTLS com certificado
    - Incluir header Content-Type: application/json
    - Se dry_run=True, simular envio sem fazer requisição real
    - Processar resposta e retornar RespostaAPI
    - Capturar e tratar erros de rede
    - _Requisitos: 6.9, 11.1, 11.2, 20.4, 21.3, 21.7_
  
  - [x] 9.4 Implementar método `APIClient.consultar_nfse()`
    - Fazer GET para endpoint /nfse/{chaveAcesso}
    - Usar autenticação mTLS
    - Processar resposta e retornar RespostaAPI
    - _Requisitos: 21.4_
  
  - [x] 9.5 Implementar método `APIClient.baixar_danfse()`
    - Fazer GET para endpoint /danfse/{chaveAcesso}
    - Usar autenticação mTLS
    - Retornar bytes do PDF
    - _Requisitos: 21.5_
  
  - [ ]* 9.6 Escrever testes property-based para comportamento dry-run
    - **Property 5: Comportamento Dry-Run**
    - **Valida: Requisitos 6.9, 6.12, 13.5**
  
  - [ ]* 9.7 Escrever testes unitários para api_client
    - Testar emissão com mocks de resposta da API
    - Testar consulta com mocks
    - Testar download de DANFSe com mocks
    - Testar tratamento de erros de rede
    - Testar modo dry-run (verificar que não faz requisições)
    - _Requisitos: 16.4, 16.5, 16.6_

- [x] 10. Implementar módulo de logging (logger.py)
  - [x] 10.1 Criar dataclass `LogEmissao`
    - Implementar campos: timestamp, ambiente, dry_run, prestador, tomador, servico, valor, data_emissao, id_dps, resposta_api, metadados
    - Implementar método `para_dict()`
    - Implementar método `salvar()` que salva JSON formatado
    - _Requisitos: 15.1, 15.4_
  
  - [x] 10.2 Implementar função `criar_log_emissao()`
    - Criar objeto LogEmissao a partir dos dados da operação
    - Incluir resposta completa da API
    - Incluir indicador de dry_run se aplicável
    - _Requisitos: 15.1, 15.2, 15.3, 15.6_
  
  - [x] 10.3 Implementar função `obter_metadados()`
    - Obter versão do Python
    - Obter sistema operacional
    - Obter versão do nfse-cli
    - _Requisitos: 15.7_
  
  - [ ]* 10.4 Escrever testes property-based para estrutura de log
    - **Property 12: Estrutura Completa de Log**
    - **Valida: Requisitos 15.1, 15.4**
  
  - [ ]* 10.5 Escrever testes unitários para logger
    - Testar criação de log com dados completos
    - Testar salvamento de log formatado
    - Testar obtenção de metadados
    - _Requisitos: 16.1_

- [x] 11. Checkpoint - Validar módulos core
  - Garantir que todos os testes passam
  - Verificar integração entre módulos
  - Perguntar ao usuário se há dúvidas ou ajustes necessários


- [x] 12. Implementar módulo CLI (cli.py)
  - [x] 12.1 Implementar função `criar_parser()`
    - Criar parser principal com argparse
    - Adicionar argumentos globais: --verbose, --silent
    - Criar subparsers para comandos: init, emitir, danfse, importar
    - _Requisitos: 7.7, 19.1_
  
  - [x] 12.2 Configurar subparser do comando `init`
    - Sem parâmetros obrigatórios
    - _Requisitos: 1.1_
  
  - [x] 12.3 Configurar subparser do comando `emitir`
    - Parâmetro obrigatório: --valor
    - Parâmetros opcionais: --data, --ambiente, --dry-run, --prestador, --tomador, --servico
    - _Requisitos: 5.1, 5.3, 6.3, 6.6, 17.1_
  
  - [x] 12.4 Configurar subparser do comando `danfse`
    - Parâmetro obrigatório: chave_acesso (posicional)
    - _Requisitos: 8.1_
  
  - [x] 12.5 Configurar subparser do comando `importar`
    - Parâmetro obrigatório: chave_acesso (posicional)
    - _Requisitos: 9.1_
  
  - [x] 12.6 Implementar função `configurar_output()`
    - Configurar modo verbose/silent baseado em argumentos
    - Verbose tem precedência sobre silent
    - _Requisitos: 7.7, 19.7_
  
  - [x] 12.7 Implementar função `main()`
    - Parsear argumentos
    - Configurar output
    - Chamar função apropriada baseada no comando
    - Capturar exceções e retornar códigos de saída apropriados
    - _Requisitos: 11.6_
  
  - [ ]* 12.8 Escrever testes property-based para modo verbose
    - **Property 14: Modo Verbose Exibe XML**
    - **Valida: Requisitos 19.2**
  
  - [ ]* 12.9 Escrever testes property-based para modo silencioso
    - **Property 6: Modo Silencioso**
    - **Valida: Requisitos 7.7**
  
  - [ ]* 12.10 Escrever testes property-based para códigos de saída
    - **Property 10: Código de Saída em Erros**
    - **Valida: Requisitos 11.6**
  
  - [ ]* 12.11 Escrever testes unitários para CLI
    - Testar parsing de argumentos
    - Testar precedência verbose sobre silent
    - Testar códigos de saída
    - _Requisitos: 16.1_

- [x] 13. Implementar comando `init` (cli.py)
  - [x] 13.1 Implementar função `executar_init()`
    - Criar todos os diretórios necessários
    - Perguntar se deseja inserir dados da empresa
    - Se sim, coletar dados interativamente (CNPJ, nome, cMun, cServ, IM, email)
    - Coletar dados do regime tributário (opSimpNac, regEspTrib, regApTribSN)
    - Salvar arquivo prestador_{cnpj}.json
    - Perguntar se deseja definir como padrão
    - Se sim, atualizar config.json
    - Perguntar se deseja inserir dados do serviço
    - Se sim, coletar dados interativamente (descrição, cTribNac)
    - Salvar arquivo servico_{codigo}.json
    - Perguntar se deseja definir como padrão
    - Se sim, atualizar config.json
    - Criar config.json com valores padrão se não existir
    - Não sobrescrever config.json existente
    - Exibir mensagem de sucesso com lista de arquivos criados
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14_
  
  - [ ]* 13.2 Escrever testes property-based para formato de arquivo de prestador
    - **Property 16: Formato de Nome de Arquivo de Prestador**
    - **Valida: Requisitos 1.4**
  
  - [ ]* 13.3 Escrever testes property-based para formato de arquivo de serviço
    - **Property 17: Formato de Nome de Arquivo de Serviço**
    - **Valida: Requisitos 1.9**
  
  - [ ]* 13.4 Escrever testes unitários para comando init
    - Testar criação de diretórios
    - Testar fluxo interativo (com mocks de input)
    - Testar criação de arquivos JSON
    - Testar atualização de config.json
    - _Requisitos: 16.1_


- [x] 14. Implementar comando `emitir` (cli.py)
  - [x] 14.1 Implementar função `executar_emitir()`
    - Carregar config.json
    - Aplicar overrides de ambiente e dry_run se fornecidos via CLI
    - Validar que --valor foi fornecido
    - Validar que --data foi fornecido
    - Validar formato de data (ISO 8601)
    - Carregar e validar certificado digital
    - Exibir informações do certificado (exceto em modo silencioso)
    - Carregar arquivos JSON de prestador, tomador e serviço
    - Usar defaults do config.json se não fornecidos via CLI
    - Validar dados de prestador, tomador e serviço
    - Validar valor positivo
    - Validar regras de incidência do ISSQN
    - Gerar ID do DPS
    - Construir XML do DPS
    - Assinar XML com certificado
    - Salvar DPS no diretório dps/
    - Comprimir XML (Gzip + Base64)
    - Se dry_run: simular envio, salvar log, exibir mensagem, parar
    - Se não dry_run: enviar para API via mTLS
    - Processar resposta da API
    - Salvar NFS-e no diretório nfse/
    - Salvar log estruturado no diretório logs/
    - Exibir resultado com chave de acesso
    - Exibir mensagens informativas em cada etapa (exceto em modo silencioso)
    - Exibir XML e payload em modo verbose
    - Tratar erros e retornar códigos de saída apropriados
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 10.1, 10.2, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 13.1, 13.2, 13.3, 13.4, 13.5, 17.1, 17.4, 19.2, 19.3, 19.4, 19.5, 19.6_
  
  - [ ]* 14.2 Escrever testes property-based para validação de regime tributário
    - **Property 18: Validação de Regime Tributário**
    - **Valida: Requisitos 4.1, 4.9**
  
  - [ ]* 14.3 Escrever testes property-based para DPS com assinatura
    - **Property 11: DPS com Assinatura Digital**
    - **Valida: Requisitos 13.3**
  
  - [ ]* 14.4 Escrever testes unitários para comando emitir
    - Testar fluxo completo com mocks
    - Testar modo dry-run
    - Testar tratamento de erros
    - Testar salvamento de arquivos
    - _Requisitos: 16.4, 16.5_

- [x] 15. Implementar comando `danfse` (cli.py)
  - [x] 15.1 Implementar função `executar_danfse()`
    - Carregar config.json
    - Validar e carregar certificado digital
    - Tentar consultar NFS-e para obter dados do prestador e tomador (com fallback)
    - Fazer requisição GET para /danfse/{chaveAcesso} via mTLS
    - Salvar PDF no diretório danfse/ com nome completo se dados disponíveis, ou simplificado caso contrário
    - Formato completo: {timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.pdf
    - Formato simplificado: {timestamp}_{chave_acesso}.pdf
    - NÃO criar arquivo de log
    - Exibir mensagem de sucesso com caminho do arquivo
    - Exibir aviso se não conseguir extrair dados da NFS-e
    - Exibir mensagem de erro no console se falhar (sem criar log)
    - _Requisitos: 3.3, 8.1, 8.2, 8.3, 8.5, 8.6, 8.7, 8.8_
  
  - [ ]* 15.2 Escrever testes unitários para comando danfse
    - Testar download com mock de resposta da API
    - Testar que não cria arquivo de log
    - Testar tratamento de erros
    - _Requisitos: 16.4_

- [x] 16. Implementar comando `importar` (cli.py)
  - [x] 16.1 Implementar função `executar_importar()`
    - Carregar config.json
    - Validar e carregar certificado digital
    - Fazer requisição GET para /nfse/{chaveAcesso} via mTLS
    - Descomprimir XML da NFS-e (Base64 + Gzip)
    - Parsear XML da NFS-e
    - Extrair dados do prestador e salvar em prestadores/prestador_{timestamp}.json
    - Extrair dados do tomador e salvar em tomadores/tomador_{timestamp}.json
    - Extrair dados do serviço e salvar em servicos/servico_{timestamp}.json
    - Usar chaves compatíveis com tags XML oficiais
    - Exibir mensagens informativas com caminhos dos arquivos criados
    - Exibir mensagem de erro clara se falhar
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  
  - [ ]* 16.2 Escrever testes unitários para comando importar
    - Testar importação com mock de resposta da API
    - Testar parsing de XML
    - Testar criação de arquivos JSON
    - Testar tratamento de erros
    - _Requisitos: 16.4_

- [x] 17. Checkpoint - Validar comandos CLI
  - Garantir que todos os testes passam
  - Testar comandos manualmente em modo dry-run
  - Perguntar ao usuário se há dúvidas ou ajustes necessários


- [x] 18. Criar entry point principal (nfse.py)
  - [x] 18.1 Criar arquivo nfse.py na raiz do projeto
    - Importar função main de nfse_core.cli
    - Adicionar shebang para execução direta
    - Adicionar bloco if __name__ == '__main__'
    - Chamar main() e capturar código de saída
    - _Requisitos: técnicos_
  
  - [ ]* 18.2 Escrever testes de integração end-to-end
    - Testar fluxo completo de init
    - Testar fluxo completo de emitir em dry-run
    - Testar fluxo completo de importar (com mocks)
    - _Requisitos: 16.4_

- [x] 19. Implementar suporte a caminhos com subdiretórios
  - [x] 19.1 Atualizar funções de carregamento de arquivos
    - Garantir que métodos `carregar()` dos modelos aceitam caminhos relativos
    - Validar existência do arquivo antes de tentar ler
    - Exibir mensagem de erro clara se arquivo não existir
    - _Requisitos: 17.1, 17.2, 17.3, 17.4_
  
  - [ ]* 19.2 Escrever testes property-based para caminhos com subdiretórios
    - **Property 13: Aceitação de Caminhos com Subdiretórios**
    - **Valida: Requisitos 17.1**
  
  - [ ]* 19.3 Escrever testes unitários para caminhos com subdiretórios
    - Testar carregamento de arquivos em subdiretórios
    - Testar validação de existência de arquivos
    - _Requisitos: 16.1_

- [x] 20. Implementar validações oficiais obrigatórias
  - [x] 20.1 Adicionar validação de alíquotas ao fluxo de emissão
    - Integrar validações de alíquota máxima e mínima
    - Exibir mensagens de erro claras quando limites são violados
    - _Requisitos: 22.1, 22.2, 22.3, 22.4_
  
  - [x] 20.2 Adicionar validação de regras de incidência ao fluxo de emissão
    - Integrar validação de local de incidência baseada no código de serviço
    - Exibir mensagens de erro claras explicando a regra esperada
    - _Requisitos: 24.1, 24.2, 24.3, 24.4, 24.5_
  
  - [x] 20.3 Implementar suporte opcional ao grupo IBSCBS
    - Adicionar campos IBSCBS aos modelos de dados
    - Implementar lógica de obrigatoriedade baseada em regime tributário e data
    - Incluir grupo IBSCBS no XML do DPS quando fornecido
    - Validar obrigatoriedade antes de enviar
    - _Requisitos: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_
  
  - [ ]* 20.4 Escrever testes unitários para validações oficiais
    - Testar validação de alíquotas
    - Testar validação de regras de incidência
    - Testar obrigatoriedade de IBSCBS
    - _Requisitos: 16.1_

- [x] 21. Criar arquivos de exemplo e documentação
  - [x] 21.1 Criar arquivos JSON de exemplo
    - Criar exemplo de prestador_{cnpj}.json com comentários explicativos
    - Criar exemplo de tomador_{documento}.json com comentários explicativos
    - Criar exemplo de servico_{codigo}.json com comentários explicativos
    - Criar exemplo de config.json com comentários explicativos
    - Todos os exemplos devem usar chaves compatíveis com tags XML
    - _Requisitos: 4.6, 14.4_
  
  - [x] 21.2 Atualizar README.md
    - Adicionar seção de instalação com dependências
    - Adicionar exemplos de uso de todos os comandos (init, emitir, danfse, importar)
    - Explicar estrutura de diretórios e propósito de cada pasta
    - Explicar formato de parâmetros de linha de comando
    - Adicionar seção sobre certificado digital (como obter e configurar)
    - Explicar funcionamento do modo dry-run e quando usar
    - Adicionar seção de troubleshooting com erros comuns e soluções
    - Manter comentários explicativos existentes no código
    - _Requisitos: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

- [x] 22. Checkpoint final - Validação completa
  - Executar todos os testes (unitários e property-based)
  - Verificar cobertura de testes (objetivo: mínimo 80%)
  - Testar todos os comandos manualmente
  - Validar documentação e exemplos
  - Perguntar ao usuário se há ajustes finais necessários


## Notas

### Sobre Tarefas Opcionais

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Todas as tarefas de testes (unitários e property-based) são marcadas como opcionais
- No entanto, é altamente recomendado implementar os testes para garantir a qualidade do código

### Sobre Property-Based Testing

- Cada property test deve executar mínimo 100 iterações
- Cada property test deve incluir tag de referência ao design no formato:
  ```python
  """
  Feature: nfse-cli-refactoring, Property N: [Título da Propriedade]
  
  [Descrição da propriedade]
  """
  ```
- Use o framework Hypothesis para Python
- Configure no conftest.py: `settings.register_profile("default", max_examples=100)`

### Sobre Testes Unitários

- Foque em casos específicos, exemplos concretos e edge cases
- Use pytest-mock para mockar chamadas externas (API, arquivos, etc)
- Use fixtures para dados de teste reutilizáveis
- Organize testes por módulo (test_validation.py, test_xml_builder.py, etc)

### Sobre Checkpoints

- Checkpoints são momentos para validar o progresso e garantir que tudo está funcionando
- Em cada checkpoint, execute todos os testes e verifique se passam
- Pergunte ao usuário se há dúvidas ou ajustes necessários antes de prosseguir

### Ordem de Implementação

A ordem das tarefas foi cuidadosamente planejada para:
1. Estabelecer a base (estrutura, modelos, validações)
2. Implementar funcionalidades core (XML, crypto, API)
3. Implementar comandos CLI em ordem de dependência
4. Adicionar validações oficiais e suporte completo
5. Finalizar com documentação e exemplos

### Prioridades

**Alta Prioridade (MVP):**
- Tarefas 1-18: Estrutura base e comandos principais
- Validações básicas de dados
- Modo dry-run funcional

**Média Prioridade:**
- Tarefas 19-20: Validações oficiais completas
- Suporte a IBSCBS
- Testes automatizados

**Baixa Prioridade:**
- Tarefa 21: Documentação detalhada
- Exemplos adicionais
- Melhorias de UX

### Referências

- **Schema Oficial**: DPS NFS-e v1.01 (20260122)
- **API Oficial**: https://adn.producaorestrita.nfse.gov.br (ambiente de testes)
- **Documentação**: Anexo I - Regras de Negócio do DPS
- **Certificação**: ICP-Brasil (certificado A1 formato PFX/PKCS#12)

### Comandos Úteis

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=nfse_core --cov-report=html --cov-report=term

# Executar apenas property tests
pytest -m property

# Executar apenas testes unitários
pytest -m unit

# Executar testes de integração
pytest -m integration

# Executar comando em modo dry-run
python nfse.py emitir --valor 1500.00 --data 2024-01-15T14:30:00-03:00 --dry-run

# Executar comando em modo verbose
python nfse.py emitir --valor 1500.00 --data 2024-01-15T14:30:00-03:00 --dry-run --verbose
```

