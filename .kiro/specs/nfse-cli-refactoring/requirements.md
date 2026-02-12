# Documento de Requisitos

## Introdução

Este documento especifica os requisitos para a refatoração e melhoria do nfse-cli, uma ferramenta de linha de comando em Python para emissão de Nota Fiscal de Serviço Eletrônica (NFS-e) do Governo Federal. O sistema atual nunca foi testado e apresenta diversos problemas de implementação, estrutura e usabilidade que precisam ser corrigidos.

## Glossário

- **Sistema**: O aplicativo nfse-cli
- **DPS**: Declaração de Prestação de Serviço (documento XML que contém os dados para emissão da NFS-e)
- **NFS-e**: Nota Fiscal de Serviço Eletrônica
- **DANFSe**: Documento Auxiliar da Nota Fiscal de Serviço Eletrônica (representação em PDF)
- **Prestador**: Empresa ou profissional que presta o serviço e emite a nota fiscal (tag XML: `prest`)
- **Tomador**: Cliente que contrata o serviço (tag XML: `toma`)
- **Certificado_Digital**: Certificado A1 no formato PFX/PKCS#12 usado para autenticação mTLS e assinatura digital
- **CLI**: Interface de Linha de Comando (Command Line Interface)
- **Chave_de_Acesso**: Identificador único de 50 dígitos de uma NFS-e
- **mTLS**: Autenticação mútua TLS (mutual TLS)
- **XMLDSig**: Assinatura digital XML
- **Diretório_Principal**: Diretório raiz onde o script nfse.py está localizado
- **Ambiente**: Ambiente de execução da API (producao ou producaorestrita)
- **Dry_Run**: Modo de simulação onde o Sistema executa todas as operações exceto o envio real para a API
- **Sefin_Nacional**: Sistema Nacional de Nota Fiscal de Serviço Eletrônica (API oficial do governo)
- **cTribNac**: Código de Tributação Nacional (6 dígitos numéricos que identifica o serviço na lista nacional)
- **cMun**: Código do município IBGE (7 dígitos)
- **IBSCBS**: Grupo de informações do IBS (Imposto sobre Bens e Serviços) e CBS (Contribuição sobre Bens e Serviços) - opcional até 2027 para optantes do Simples Nacional
- **Base64_Gzip**: Formato de compressão e codificação usado para enviar o XML da DPS para a API (XML → Gzip → Base64)

## Requisitos

### Requisito 1: Comando de Inicialização do Sistema

**User Story:** Como novo usuário do sistema, eu quero executar um comando de inicialização que configure toda a estrutura necessária e colete dados iniciais, para que eu possa começar a usar o sistema rapidamente.

#### Critérios de Aceitação

1. QUANDO o comando `init` é executado, ENTÃO o Sistema DEVE criar automaticamente os seguintes diretórios no Diretório_Principal caso não existam: `cert/`, `logs/`, `prestadores/`, `tomadores/`, `servicos/`, `danfse/`, `nfse/`, `dps/`
2. QUANDO o comando `init` é executado, ENTÃO o Sistema DEVE perguntar ao usuário se deseja inserir dados iniciais da empresa
3. QUANDO o usuário confirma inserção de dados da empresa, ENTÃO o Sistema DEVE solicitar interativamente: CNPJ, nome/razão social, código do município IBGE, código do serviço, inscrição municipal (opcional), e email (opcional)
4. QUANDO os dados da empresa são coletados, ENTÃO o Sistema DEVE salvar um arquivo JSON no diretório `prestadores/` com nome `prestador_{cnpj}.json`
5. QUANDO o arquivo do prestador é gerado, ENTÃO o Sistema DEVE perguntar ao usuário se deseja definir este arquivo como prestador padrão no `config.json`
6. QUANDO o usuário confirma definir como padrão, ENTÃO o Sistema DEVE atualizar a chave `defaults.prestador` no `config.json` com o caminho do arquivo gerado
7. QUANDO o comando `init` é executado, ENTÃO o Sistema DEVE perguntar ao usuário se deseja inserir dados do serviço principal
8. QUANDO o usuário confirma inserção de dados do serviço, ENTÃO o Sistema DEVE solicitar interativamente: descrição do serviço e código de tributação nacional
9. QUANDO os dados do serviço são coletados, ENTÃO o Sistema DEVE salvar um arquivo JSON no diretório `servicos/` com nome `servico_{codigo_tributacao_nacional}.json` onde o código de tributação nacional tem os pontos removidos
10. QUANDO o arquivo do serviço é gerado, ENTÃO o Sistema DEVE perguntar ao usuário se deseja definir este arquivo como serviço padrão no `config.json`
11. QUANDO o usuário confirma definir como padrão, ENTÃO o Sistema DEVE atualizar a chave `defaults.servicos` no `config.json` com o caminho do arquivo gerado
12. QUANDO o comando `init` é executado, ENTÃO o Sistema DEVE criar o arquivo `config.json` caso não exista, com valores padrão incluindo `ambiente: "producaorestrita"` e `dry_run: true`
13. QUANDO o comando `init` é executado e o arquivo `config.json` já existe, ENTÃO o Sistema NÃO DEVE sobrescrever o arquivo existente, mas DEVE permitir atualizar as chaves de defaults se novos arquivos forem criados
14. QUANDO o comando `init` é concluído, ENTÃO o Sistema DEVE exibir mensagem de sucesso listando todos os diretórios e arquivos criados

### Requisito 2: Gerenciamento Automático de Estrutura de Diretórios

**User Story:** Como usuário do sistema, eu quero que todos os diretórios necessários sejam criados automaticamente quando necessário, para que eu não precise me preocupar com a estrutura de pastas.

#### Critérios de Aceitação

1. QUANDO qualquer comando do Sistema precisa salvar um arquivo, ENTÃO o Sistema DEVE verificar se o diretório de destino existe e criá-lo caso necessário
2. QUANDO os diretórios são criados automaticamente, ENTÃO o Sistema DEVE continuar a execução normalmente sem interromper o fluxo do usuário
3. QUANDO os diretórios são criados automaticamente, ENTÃO o Sistema DEVE exibir mensagem informativa sobre a criação (exceto se modo silencioso estiver ativo)

### Requisito 3: Padronização de Nomes de Arquivos

**User Story:** Como usuário do sistema, eu quero que todos os arquivos relacionados tenham nomes padronizados e rastreáveis, para que eu possa facilmente identificar e correlacionar arquivos de uma mesma operação.

#### Critérios de Aceitação

1. QUANDO o Sistema gera qualquer arquivo de saída relacionado a uma emissão, ENTÃO o Sistema DEVE usar o formato de nome: `{timestamp}_{cnpj_prestador}_{documento_tomador}.{extensao}` onde timestamp está no formato `YYYYMMDD_HHMMSS`
2. QUANDO o Sistema salva arquivos relacionados à mesma operação de emissão, ENTÃO o Sistema DEVE usar o mesmo nome base (timestamp + identificadores) diferindo apenas na extensão do arquivo
3. QUANDO o Sistema baixa um DANFSe, ENTÃO o Sistema DEVE tentar consultar a NFS-e para obter os dados do prestador e tomador; se bem-sucedido, salvar com o nome `{timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.pdf`; caso contrário, salvar com o nome `{timestamp}_{chave_acesso}.pdf` no diretório `danfse/`
4. QUANDO o Sistema salva um XML de NFS-e emitida, ENTÃO o Sistema DEVE salvar no diretório `nfse/` com o nome padronizado
5. QUANDO o Sistema salva um log de operação de emissão, ENTÃO o Sistema DEVE salvar no diretório `logs/` com o mesmo nome base do arquivo relacionado, diferindo apenas pela extensão `.json`
6. QUANDO o Sistema salva um XML de DPS antes do envio, ENTÃO o Sistema DEVE salvar no diretório `dps/` com o nome padronizado

### Requisito 4: Compatibilidade com Tags XML Oficiais do DPS

**User Story:** Como desenvolvedor que usa o sistema, eu quero que os campos dos arquivos JSON correspondam exatamente às tags XML oficiais do DPS, para que a estrutura seja consistente e fácil de entender.

#### Critérios de Aceitação

1. QUANDO o arquivo JSON do prestador é lido, ENTÃO ele DEVE usar as seguintes chaves correspondentes às tags XML: `CNPJ` ou `CPF`, `xNome`, `IM` (opcional), `cMun`, `email` (opcional), e `regTrib` (objeto obrigatório com regime tributário contendo `opSimpNac`, `regApTribSN` opcional, e `regEspTrib`)
2. QUANDO o arquivo JSON do tomador é lido, ENTÃO ele DEVE usar as seguintes chaves correspondentes às tags XML: `CNPJ` ou `CPF`, `xNome`, `email` (opcional), e `end` (objeto com endereço)
3. QUANDO o objeto de endereço do tomador é lido, ENTÃO ele DEVE usar as chaves: `xLgr` (logradouro), `nro` (número), `xBairro`, `cMun` (código município), `CEP`
4. QUANDO o arquivo JSON do serviço é lido, ENTÃO ele DEVE usar as chaves: `xDescServ` (descrição completa do serviço), `cTribNac` (código tributação nacional de 6 dígitos numéricos), `cTribMun` (código tributação municipal de 3 dígitos, opcional), `cNBS` (código NBS, opcional), e `cLocPrestacao` (código município IBGE onde o serviço foi prestado)
5. QUANDO o Sistema monta o XML do DPS, ENTÃO ele DEVE mapear diretamente as chaves JSON para as tags XML sem transformações
6. QUANDO arquivos de exemplo são fornecidos, ENTÃO eles DEVEM usar as chaves compatíveis com as tags XML oficiais
7. QUANDO o arquivo JSON do serviço é fornecido, ENTÃO ele NÃO DEVE conter os campos `vServ` (valor) ou `dhEmi` (data/hora) pois estes devem vir da linha de comando
8. QUANDO o Sistema monta o XML do DPS, ENTÃO ele DEVE incluir os campos obrigatórios: `tpAmb` (tipo de ambiente), `verAplic` (versão da aplicação), `serie` (série do DPS), `nDPS` (número do DPS), `dCompet` (data de competência), `dhEmi` (data/hora de emissão), `tpEmit` (tipo de emitente), e `cLocEmi` (código do local de emissão)
9. QUANDO o Sistema monta o XML do DPS, ENTÃO ele DEVE incluir a estrutura `regTrib` do prestador com os campos obrigatórios `opSimpNac` (1, 2 ou 3) e `regEspTrib` (0-6 ou 9), e o campo opcional `regApTribSN` (1, 2 ou 3) quando `opSimpNac` for 3

### Requisito 5: Parâmetros de Linha de Comando para Valor e Data

**User Story:** Como usuário do sistema, eu quero fornecer o valor e a data do serviço sempre pela linha de comando, para que eu possa emitir notas com valores e datas diferentes sem modificar arquivos JSON.

#### Critérios de Aceitação

1. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE aceitar o parâmetro obrigatório `--valor` com o valor monetário do serviço
2. QUANDO o comando `emitir` é executado sem o parâmetro `--valor`, ENTÃO o Sistema DEVE exibir uma mensagem de erro e não prosseguir com a emissão
3. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE aceitar o parâmetro obrigatório `--data` no formato ISO 8601 (YYYY-MM-DDTHH:MM:SS-03:00)
4. QUANDO o comando `emitir` é executado sem o parâmetro `--data`, ENTÃO o Sistema DEVE exibir uma mensagem de erro e não prosseguir com a emissão
5. QUANDO o Sistema lê arquivos JSON de serviço, ENTÃO o Sistema NÃO DEVE esperar ou usar campos `vServ` ou `dhEmi` desses arquivos
6. QUANDO o Sistema monta o XML da DPS, ENTÃO o Sistema DEVE usar o valor e a data fornecidos via CLI e NÃO de arquivos JSON

### Requisito 6: Configuração de Ambiente e Modo Dry-Run

**User Story:** Como usuário do sistema, eu quero poder configurar o ambiente de execução e usar modo de simulação, para que eu possa testar o sistema sem enviar dados reais para a API.

#### Critérios de Aceitação

1. QUANDO o arquivo `config.json` é criado pela primeira vez, ENTÃO ele DEVE conter a chave `ambiente` com valor padrão `"producaorestrita"`
2. QUANDO o arquivo `config.json` é criado pela primeira vez, ENTÃO ele DEVE conter a chave `dry_run` com valor padrão `true`
3. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE aceitar o parâmetro opcional `--ambiente` com valores válidos: `producao` ou `producaorestrita`
4. QUANDO o parâmetro `--ambiente` é fornecido, ENTÃO ele DEVE sobrescrever o valor configurado em `config.json` para aquela execução
5. QUANDO o parâmetro `--ambiente` NÃO é fornecido, ENTÃO o Sistema DEVE usar o valor de `ambiente` do `config.json`
6. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE aceitar o parâmetro opcional `--dry-run` (flag booleana)
7. QUANDO o parâmetro `--dry-run` é fornecido, ENTÃO ele DEVE sobrescrever o valor configurado em `config.json` para aquela execução
8. QUANDO o parâmetro `--dry-run` NÃO é fornecido, ENTÃO o Sistema DEVE usar o valor de `dry_run` do `config.json`
9. QUANDO o modo Dry_Run está ativo, ENTÃO o Sistema DEVE executar todas as operações (validação, construção de XML, assinatura, compressão) EXCETO o envio real para a API
10. QUANDO o modo Dry_Run está ativo, ENTÃO o Sistema DEVE exibir mensagem clara indicando que está em modo de simulação
11. QUANDO o modo Dry_Run está ativo, ENTÃO o Sistema DEVE salvar os arquivos DPS e logs normalmente
12. QUANDO o modo Dry_Run está ativo, ENTÃO o Sistema NÃO DEVE salvar arquivos de NFS-e (pois não houve emissão real)

### Requisito 7: Saídas Informativas em Tela

**User Story:** Como usuário do sistema, eu quero receber informações detalhadas sobre todas as operações executadas, para que eu possa acompanhar o progresso e identificar problemas.

#### Critérios de Aceitação

1. QUANDO qualquer comando do Sistema é executado, ENTÃO o Sistema DEVE exibir mensagens informativas sobre cada etapa da operação
2. QUANDO o Sistema lê um arquivo, ENTÃO ele DEVE exibir o caminho completo do arquivo lido
3. QUANDO o Sistema salva um arquivo, ENTÃO ele DEVE exibir o caminho completo do arquivo salvo
4. QUANDO o Sistema cria um diretório, ENTÃO ele DEVE exibir mensagem informando a criação
5. QUANDO o Sistema executa validações, ENTÃO ele DEVE exibir mensagem sobre o que está sendo validado
6. QUANDO o Sistema se comunica com a API, ENTÃO ele DEVE exibir a URL e o método HTTP usado
7. QUANDO o parâmetro global `--silent` ou `-s` é fornecido, ENTÃO o Sistema NÃO DEVE exibir mensagens informativas, apenas erros críticos
8. QUANDO o modo silencioso NÃO está ativo, ENTÃO o Sistema DEVE usar emojis e formatação para tornar as mensagens mais legíveis
9. QUANDO uma operação é concluída com sucesso, ENTÃO o Sistema DEVE exibir mensagem de sucesso clara com resumo da operação

### Requisito 8: Comando Importar DANFSe sem Geração de Log

**User Story:** Como usuário do sistema, eu quero baixar DANFSe sem gerar arquivos de log desnecessários, para que minha pasta de logs contenha apenas registros de operações de emissão.

#### Critérios de Aceitação

1. QUANDO o comando `danfse` é executado com sucesso, ENTÃO o Sistema DEVE salvar apenas o arquivo PDF no diretório `danfse/`
2. QUANDO o comando `danfse` é executado, ENTÃO o Sistema NÃO DEVE criar arquivo de log no diretório `logs/`
3. QUANDO o comando `danfse` falha, ENTÃO o Sistema DEVE exibir a mensagem de erro no console mas NÃO DEVE criar arquivo de log
4. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE continuar gerando logs normalmente no diretório `logs/`
5. QUANDO o comando `danfse` é executado, ENTÃO o Sistema DEVE tentar consultar a NFS-e para obter os dados do prestador e tomador
6. QUANDO a consulta da NFS-e é bem-sucedida e os dados são extraídos, ENTÃO o arquivo PDF DEVE usar o formato de nome: `{timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.pdf`
7. QUANDO a consulta da NFS-e falha ou os dados não podem ser extraídos, ENTÃO o Sistema DEVE exibir um aviso e salvar o arquivo PDF com formato simplificado: `{timestamp}_{chave_acesso}.pdf`
8. QUANDO a consulta da NFS-e falha, ENTÃO o Sistema NÃO DEVE interromper o download do PDF, apenas usar o formato de nome simplificado

### Requisito 9: Implementação do Comando Importar

**User Story:** Como usuário do sistema, eu quero importar dados de uma NFS-e existente usando sua chave de acesso, para que eu possa criar templates JSON baseados em notas já emitidas.

#### Critérios de Aceitação

1. QUANDO o comando `importar` é executado com uma Chave_de_Acesso válida, ENTÃO o Sistema DEVE fazer uma requisição à API para obter os dados da NFS-e
2. QUANDO os dados da NFS-e são obtidos com sucesso, ENTÃO o Sistema DEVE extrair as informações do prestador e salvar em `prestadores/prestador_{timestamp}.json`
3. QUANDO os dados da NFS-e são obtidos com sucesso, ENTÃO o Sistema DEVE extrair as informações do tomador e salvar em `tomadores/tomador_{timestamp}.json`
4. QUANDO os dados da NFS-e são obtidos com sucesso, ENTÃO o Sistema DEVE extrair as informações do serviço e salvar em `servicos/servico_{timestamp}.json`
5. QUANDO o comando `importar` é executado, ENTÃO o Sistema DEVE exibir mensagens informativas sobre os arquivos criados com seus caminhos completos
6. QUANDO o comando `importar` falha, ENTÃO o Sistema DEVE exibir uma mensagem de erro clara explicando o problema
7. QUANDO os arquivos JSON são gerados pelo comando `importar`, ENTÃO eles DEVEM usar as chaves compatíveis com as tags XML oficiais do DPS

### Requisito 10: Validação de Dados de Entrada

**User Story:** Como usuário do sistema, eu quero que o sistema valide os dados antes de tentar emitir uma nota, para que eu receba feedback imediato sobre erros de configuração.

#### Critérios de Aceitação

1. QUANDO o Sistema lê um arquivo JSON, ENTÃO o Sistema DEVE validar se todos os campos obrigatórios estão presentes
2. QUANDO um campo obrigatório está ausente, ENTÃO o Sistema DEVE exibir uma mensagem de erro específica indicando qual campo está faltando e em qual arquivo
3. QUANDO o valor fornecido via CLI é zero ou negativo, ENTÃO o Sistema DEVE rejeitar a operação com mensagem de erro
4. QUANDO o CNPJ do prestador é fornecido, ENTÃO o Sistema DEVE validar se tem 14 dígitos numéricos e verificar o dígito verificador (DV)
5. QUANDO o CPF do prestador é fornecido, ENTÃO o Sistema DEVE validar se tem 11 dígitos numéricos e verificar o dígito verificador (DV)
6. QUANDO o documento do tomador (CPF ou CNPJ) é fornecido, ENTÃO o Sistema DEVE validar o formato e verificar o dígito verificador (DV)
7. QUANDO o código de município (cMun) é fornecido, ENTÃO o Sistema DEVE validar se tem exatamente 7 dígitos numéricos
8. QUANDO o código de tributação nacional (cTribNac) é fornecido, ENTÃO o Sistema DEVE validar se tem exatamente 6 dígitos numéricos
9. QUANDO o arquivo de certificado PFX não existe, ENTÃO o Sistema DEVE exibir mensagem de erro clara antes de tentar carregar
10. QUANDO a senha do certificado está incorreta, ENTÃO o Sistema DEVE capturar a exceção e exibir mensagem de erro amigável

### Requisito 11: Tratamento Robusto de Erros

**User Story:** Como usuário do sistema, eu quero receber mensagens de erro claras e úteis quando algo dá errado, para que eu possa corrigir o problema rapidamente.

#### Critérios de Aceitação

1. QUANDO ocorre um erro de rede durante a comunicação com a API, ENTÃO o Sistema DEVE capturar a exceção e exibir mensagem explicativa
2. QUANDO a API retorna um erro (status code diferente de 200/201), ENTÃO o Sistema DEVE exibir o código de status e a mensagem de erro retornada pela API
3. QUANDO ocorre um erro ao ler um arquivo JSON, ENTÃO o Sistema DEVE exibir o nome do arquivo e a descrição do erro de parsing
4. QUANDO ocorre um erro ao assinar o XML, ENTÃO o Sistema DEVE capturar a exceção e exibir mensagem explicativa
5. QUANDO ocorre um erro ao salvar um arquivo, ENTÃO o Sistema DEVE exibir o caminho do arquivo e a descrição do erro
6. QUANDO qualquer operação falha, ENTÃO o Sistema DEVE retornar um código de saída diferente de zero para permitir automação
7. QUANDO ocorre um erro, ENTÃO o Sistema NÃO DEVE exibir stack traces completos para o usuário final, apenas mensagens amigáveis (exceto se modo verbose estiver ativo)

### Requisito 12: Separação de Responsabilidades no Código

**User Story:** Como desenvolvedor que mantém o sistema, eu quero que o código tenha responsabilidades bem separadas, para que seja mais fácil entender, testar e modificar.

#### Critérios de Aceitação

1. QUANDO o Sistema é organizado, ENTÃO o Sistema DEVE ter funções separadas para: validação de dados, leitura de arquivos, construção de XML, assinatura, comunicação com API, e salvamento de arquivos
2. QUANDO uma função é implementada, ENTÃO ela DEVE ter uma única responsabilidade clara
3. QUANDO lógica de negócio é implementada, ENTÃO ela NÃO DEVE estar misturada com código de I/O (leitura/escrita de arquivos)
4. QUANDO funções de comunicação com API são implementadas, ENTÃO elas DEVEM estar separadas da lógica de construção de payloads
5. QUANDO o código de CLI é implementado, ENTÃO ele DEVE apenas fazer parsing de argumentos e chamar funções de negócio, sem conter lógica complexa

### Requisito 13: Salvamento de DPS Original

**User Story:** Como usuário do sistema, eu quero que o XML da DPS enviada seja salvo antes da transmissão, para que eu tenha um registro completo de auditoria do que foi enviado.

#### Critérios de Aceitação

1. QUANDO o Sistema gera e assina o XML da DPS, ENTÃO o Sistema DEVE salvar uma cópia no diretório `dps/` antes de enviar para a API
2. QUANDO o arquivo DPS é salvo, ENTÃO ele DEVE usar o nome padronizado: `{timestamp}_{cnpj_prestador}_{documento_tomador}.xml`
3. QUANDO o arquivo DPS é salvo, ENTÃO ele DEVE conter o XML completo com a assinatura digital
4. QUANDO ocorre erro no envio para a API, ENTÃO o arquivo DPS DEVE estar disponível para análise e reenvio manual
5. QUANDO o modo Dry_Run está ativo, ENTÃO o arquivo DPS DEVE ser salvo normalmente

### Requisito 14: Melhoria da Documentação

**User Story:** Como novo usuário do sistema, eu quero ter documentação clara e completa, para que eu possa configurar e usar o sistema sem dificuldades.

#### Critérios de Aceitação

1. QUANDO o README.md é fornecido, ENTÃO ele DEVE conter exemplos de uso de todos os comandos disponíveis: `init`, `emitir`, `danfse`, e `importar`
2. QUANDO o README.md é fornecido, ENTÃO ele DEVE explicar claramente a estrutura de diretórios e o propósito de cada pasta
3. QUANDO o README.md é fornecido, ENTÃO ele DEVE incluir uma seção de troubleshooting com erros comuns e suas soluções
4. QUANDO arquivos de exemplo são fornecidos, ENTÃO eles DEVEM conter comentários explicando cada campo e sua correspondência com as tags XML
5. QUANDO o README.md é fornecido, ENTÃO ele DEVE explicar o formato esperado para cada parâmetro de linha de comando
6. QUANDO o README.md é fornecido, ENTÃO ele DEVE incluir informações sobre como obter e configurar o Certificado_Digital
7. QUANDO o README.md é fornecido, ENTÃO ele DEVE explicar o funcionamento do modo Dry_Run e quando usá-lo
8. QUANDO o código fonte é fornecido, ENTÃO ele DEVE manter os comentários explicativos existentes e adicionar comentários onde necessário

### Requisito 15: Logging Estruturado e Completo

**User Story:** Como usuário do sistema, eu quero que os logs sejam estruturados e contenham todas as informações relevantes, para que eu possa auditar operações e diagnosticar problemas.

#### Critérios de Aceitação

1. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE salvar um log JSON contendo: timestamp da operação, ambiente usado, modo dry_run, todos os dados do prestador (do JSON), todos os dados do tomador (do JSON), todos os dados do serviço (do JSON), valor fornecido via CLI, data de emissão, ID da DPS gerado, e resposta completa da API
2. QUANDO a emissão é bem-sucedida, ENTÃO o log DEVE incluir: chave de acesso da NFS-e emitida, código de status HTTP, versão do aplicativo da API, e data/hora de processamento retornada pela API
3. QUANDO a emissão falha, ENTÃO o log DEVE incluir: código de erro HTTP, mensagem de erro completa, e stack trace (se disponível)
4. QUANDO o log é salvo, ENTÃO ele DEVE estar formatado com indentação (pretty-printed) para facilitar leitura humana
5. QUANDO o log é salvo, ENTÃO ele DEVE usar o mesmo nome base dos arquivos XML relacionados
6. QUANDO o modo Dry_Run está ativo, ENTÃO o log DEVE incluir um campo indicando que foi uma simulação
7. QUANDO metadados relevantes estão disponíveis (versão do sistema, versão do Python, etc.), ENTÃO eles DEVEM ser incluídos no log

### Requisito 16: Configuração de Ambiente de Testes

**User Story:** Como desenvolvedor do sistema, eu quero ter testes automatizados, para que eu possa garantir que o código funciona corretamente e prevenir regressões.

#### Critérios de Aceitação

1. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir testes unitários para funções de validação de dados
2. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir testes unitários para funções de construção de XML
3. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir testes unitários para funções de formatação de nomes de arquivos
4. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir testes de integração que simulam chamadas à API usando mocks
5. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir testes específicos para validar operações em modo Dry_Run
6. QUANDO testes em modo Dry_Run são executados, ENTÃO eles DEVEM verificar que nenhuma chamada real à API foi feita
7. QUANDO testes em modo Dry_Run são executados, ENTÃO eles DEVEM verificar que arquivos DPS e logs foram salvos corretamente
8. QUANDO testes são executados, ENTÃO eles NÃO DEVEM depender de arquivos reais de certificado ou fazer chamadas reais à API
9. QUANDO testes são executados, ENTÃO eles DEVEM usar fixtures e dados de exemplo para simular cenários reais
10. QUANDO o Sistema é desenvolvido, ENTÃO ele DEVE incluir um arquivo `requirements-dev.txt` com dependências de teste (pytest, pytest-mock, etc.)

### Requisito 17: Suporte a Múltiplos Prestadores e Tomadores

**User Story:** Como usuário que gerencia múltiplos clientes, eu quero poder organizar arquivos de prestadores e tomadores em subdiretórios, para que eu possa manter uma estrutura organizada.

#### Critérios de Aceitação

1. QUANDO o parâmetro `--prestador` é fornecido, ENTÃO o Sistema DEVE aceitar caminhos relativos incluindo subdiretórios (ex: `prestadores/empresa_a/prestador.json`)
2. QUANDO o parâmetro `--tomador` é fornecido, ENTÃO o Sistema DEVE aceitar caminhos relativos incluindo subdiretórios (ex: `tomadores/clientes/cliente_especial.json`)
3. QUANDO o parâmetro `--servico` é fornecido, ENTÃO o Sistema DEVE aceitar caminhos relativos incluindo subdiretórios
4. QUANDO caminhos com subdiretórios são usados, ENTÃO o Sistema DEVE validar a existência do arquivo antes de tentar ler

### Requisito 18: Validação de Certificado Digital

**User Story:** Como usuário do sistema, eu quero que o sistema valide meu certificado digital antes de tentar emitir notas, para que eu seja alertado sobre problemas de certificado antes de iniciar o processo.

#### Critérios de Aceitação

1. QUANDO o Sistema carrega o Certificado_Digital, ENTÃO o Sistema DEVE verificar se o certificado está dentro do prazo de validade
2. QUANDO o certificado está expirado, ENTÃO o Sistema DEVE exibir mensagem de erro clara com a data de expiração
3. QUANDO o certificado está próximo de expirar (menos de 30 dias), ENTÃO o Sistema DEVE exibir um aviso mas permitir a operação
4. QUANDO o Sistema carrega o Certificado_Digital, ENTÃO o Sistema DEVE verificar se a Autoridade Certificadora raiz é a AC ICP-Brasil (verificando a cadeia de certificação)
5. QUANDO o certificado NÃO é emitido pela ICP-Brasil, ENTÃO o Sistema DEVE exibir mensagem de erro clara indicando que apenas certificados ICP-Brasil são aceitos
6. QUANDO o certificado é carregado com sucesso e todas as validações passam, ENTÃO o Sistema DEVE exibir informações básicas: titular, validade, e emissor (exceto se modo silencioso estiver ativo)
7. QUANDO a senha do certificado está incorreta, ENTÃO o Sistema DEVE exibir mensagem de erro específica sobre senha inválida

### Requisito 19: Modo Verbose para Debugging

**User Story:** Como desenvolvedor ou usuário avançado, eu quero ter um modo verbose que mostre detalhes técnicos da operação, para que eu possa diagnosticar problemas complexos.

#### Critérios de Aceitação

1. QUANDO o parâmetro global `--verbose` ou `-v` é fornecido, ENTÃO o Sistema DEVE exibir informações detalhadas de cada etapa da operação
2. QUANDO o modo verbose está ativo, ENTÃO o Sistema DEVE exibir o XML gerado antes da assinatura
3. QUANDO o modo verbose está ativo, ENTÃO o Sistema DEVE exibir o payload comprimido em Base64
4. QUANDO o modo verbose está ativo, ENTÃO o Sistema DEVE exibir os headers HTTP da requisição e resposta
5. QUANDO o modo verbose NÃO está ativo, ENTÃO o Sistema DEVE exibir apenas mensagens essenciais de progresso e resultado
6. QUANDO o modo verbose está ativo e ocorre um erro, ENTÃO o Sistema DEVE exibir o stack trace completo
7. QUANDO o modo verbose e o modo silencioso são fornecidos simultaneamente, ENTÃO o modo verbose DEVE ter precedência

### Requisito 20: Compressão e Codificação do DPS para Envio

**User Story:** Como sistema que se comunica com a Sefin_Nacional, eu preciso comprimir e codificar o XML da DPS corretamente, para que a API aceite meu envio.

#### Critérios de Aceitação

1. QUANDO o Sistema prepara o DPS para envio, ENTÃO o Sistema DEVE assinar digitalmente o XML usando XMLDSig
2. QUANDO o XML está assinado, ENTÃO o Sistema DEVE comprimir o XML usando Gzip
3. QUANDO o XML está comprimido, ENTÃO o Sistema DEVE codificar o resultado em Base64
4. QUANDO o payload está pronto, ENTÃO o Sistema DEVE enviar via POST para o endpoint `/nfse` no formato JSON com a chave `dps` contendo o XML em Base64_Gzip
5. QUANDO o modo verbose está ativo, ENTÃO o Sistema DEVE exibir o tamanho do XML original, o tamanho após compressão, e o tamanho final em Base64

### Requisito 21: Endpoints Oficiais da API

**User Story:** Como sistema que se comunica com a Sefin_Nacional, eu preciso usar os endpoints oficiais corretos, para que minhas requisições sejam processadas adequadamente.

#### Critérios de Aceitação

1. QUANDO o ambiente é `producaorestrita`, ENTÃO o Sistema DEVE usar a URL base: `https://adn.producaorestrita.nfse.gov.br`
2. QUANDO o ambiente é `producao`, ENTÃO o Sistema DEVE usar a URL base: `https://adn.nfse.gov.br`
3. QUANDO o comando `emitir` é executado, ENTÃO o Sistema DEVE fazer POST para o endpoint `/nfse` (emissão síncrona)
4. QUANDO o comando `consultar` é executado com chave de acesso, ENTÃO o Sistema DEVE fazer GET para o endpoint `/nfse/{chaveAcesso}`
5. QUANDO o comando `danfse` é executado, ENTÃO o Sistema DEVE fazer GET para o endpoint `/danfse/{chaveAcesso}`
6. QUANDO qualquer requisição é feita, ENTÃO o Sistema DEVE usar autenticação mTLS com o Certificado_Digital configurado
7. QUANDO qualquer requisição é feita, ENTÃO o Sistema DEVE incluir o header `Content-Type: application/json` para requisições POST

### Requisito 22: Validação de Alíquotas do ISSQN

**User Story:** Como sistema que valida dados antes do envio, eu preciso verificar se as alíquotas estão dentro dos limites legais, para evitar rejeições pela API.

#### Critérios de Aceitação

1. QUANDO uma alíquota de ISSQN é informada ou calculada, ENTÃO o Sistema DEVE validar se não ultrapassa 5% (alíquota máxima legal)
2. QUANDO uma alíquota efetiva de ISSQN é calculada, ENTÃO o Sistema DEVE validar se não é inferior a 2% (alíquota mínima), exceto para os códigos de serviço específicos listados nas regras oficiais
3. QUANDO o código de tributação nacional (cTribNac) é um dos códigos com exceção à regra de alíquota mínima, ENTÃO o Sistema NÃO DEVE aplicar a validação de alíquota mínima de 2%
4. QUANDO a validação de alíquota falha, ENTÃO o Sistema DEVE exibir mensagem de erro clara indicando o limite violado e o valor fornecido

### Requisito 23: Suporte Opcional ao Grupo IBSCBS

**User Story:** Como prestador de serviço, eu quero que o sistema suporte opcionalmente as informações de IBS/CBS, para estar preparado para quando essas informações se tornarem obrigatórias.

#### Critérios de Aceitação

1. QUANDO o prestador é optante do Simples Nacional e a data de competência é anterior a 01/01/2027, ENTÃO o grupo IBSCBS DEVE ser opcional no DPS
2. QUANDO o prestador NÃO é optante do Simples Nacional, ENTÃO o grupo IBSCBS DEVE ser obrigatório no DPS
3. QUANDO a data de competência é 01/01/2027 ou posterior, ENTÃO o grupo IBSCBS DEVE ser obrigatório para todos os prestadores
4. QUANDO o arquivo JSON do serviço contém informações de IBSCBS, ENTÃO o Sistema DEVE incluir essas informações no XML do DPS
5. QUANDO o arquivo JSON do serviço NÃO contém informações de IBSCBS e elas são opcionais, ENTÃO o Sistema DEVE gerar o DPS sem o grupo IBSCBS
6. QUANDO o grupo IBSCBS é obrigatório mas não foi fornecido, ENTÃO o Sistema DEVE exibir mensagem de erro clara antes de tentar enviar

### Requisito 24: Validação de Regras de Incidência do ISSQN

**User Story:** Como sistema que valida dados, eu preciso verificar se o local de incidência do ISSQN está correto conforme o código de serviço, para evitar rejeições pela API.

#### Critérios de Aceitação

1. QUANDO o código de tributação nacional (cTribNac) indica que a incidência é no local da prestação, ENTÃO o Sistema DEVE validar se o código do local de incidência (cLocIncid) é igual ao código do local de prestação (cLocPrestacao)
2. QUANDO o código de tributação nacional indica que a incidência é no estabelecimento do prestador, ENTÃO o Sistema DEVE validar se o código do local de incidência é igual ao código do município do prestador
3. QUANDO o código de tributação nacional indica que a incidência é no domicílio do tomador, ENTÃO o Sistema DEVE validar se o código do local de incidência é igual ao código do município do tomador
4. QUANDO a tributação do ISSQN é imunidade, exportação ou não incidência, ENTÃO o Sistema NÃO DEVE exigir o código do local de incidência
5. QUANDO a validação de incidência falha, ENTÃO o Sistema DEVE exibir mensagem de erro clara explicando a regra de incidência esperada para aquele código de serviço
