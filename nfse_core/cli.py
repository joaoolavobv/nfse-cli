"""
Módulo CLI para nfse-cli

Este módulo gerencia a interface de linha de comando, incluindo parsing de argumentos
e orquestração dos comandos disponíveis.
"""

import argparse
import json
import os
import sys
from typing import Optional


# Variáveis globais para controle de output
VERBOSE = False
SILENT = False


class ArgumentParserPtBr(argparse.ArgumentParser):
    """
    ArgumentParser customizado com mensagens em português.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa o parser com traduções."""
        super().__init__(*args, **kwargs)
        # Traduzir strings padrão do argparse
        self._positionals.title = 'argumentos posicionais'
        self._optionals.title = 'opções'
    
    def error(self, message):
        """Sobrescreve o método error para traduzir mensagens."""
        # Traduzir mensagens comuns do argparse
        traducoes = {
            'the following arguments are required': 'os seguintes argumentos são obrigatórios',
            'invalid choice': 'escolha inválida',
            'expected one argument': 'esperado um argumento',
            'expected at least one argument': 'esperado pelo menos um argumento',
            'unrecognized arguments': 'argumentos não reconhecidos',
            'ambiguous option': 'opção ambígua',
            'error': 'erro',
        }
        
        # Aplicar traduções
        mensagem_traduzida = message
        for en, pt in traducoes.items():
            mensagem_traduzida = mensagem_traduzida.replace(en, pt)
        
        # Imprimir uso e sair com erro
        self.print_usage(sys.stderr)
        self.exit(2, f'{self.prog}: erro: {mensagem_traduzida}\n')
    
    def format_usage(self):
        """Sobrescreve format_usage para traduzir 'usage'."""
        usage = super().format_usage()
        return usage.replace('usage:', 'uso:')
    
    def format_help(self):
        """Sobrescreve format_help para traduzir termos."""
        help_text = super().format_help()
        traducoes = {
            'usage:': 'uso:',
            'positional arguments': 'argumentos posicionais',
            'optional arguments': 'argumentos opcionais',
            'options': 'opções',
            'show this help message and exit': 'exibe esta mensagem de ajuda e sai'
        }
        for en, pt in traducoes.items():
            help_text = help_text.replace(en, pt)
        return help_text


def criar_parser() -> ArgumentParserPtBr:
    """
    Cria e configura o parser de argumentos da CLI.
    
    Argumentos globais:
        --verbose, -v: Exibe informações detalhadas de debug
        --silent, -s: Suprime mensagens informativas (apenas erros críticos)
    
    Comandos disponíveis:
        init: Inicializa estrutura de diretórios e configuração
        emitir: Emite uma NFS-e
        danfse: Baixa o PDF (DANFSe) de uma NFS-e
        importar: Importa dados de uma NFS-e existente
    
    Returns:
        ArgumentParserPtBr configurado
    """
    parser = ArgumentParserPtBr(
        prog='nfse',
        description='Ferramenta de linha de comando para emissão de NFS-e do Governo Federal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  nfse init                                      # Inicializar estrutura
  nfse emitir --valor 1500.00 --data 2024-01-15  # Emitir nota
  nfse emitir --valor 1500.00 --data 15/01/2024 --dry-run  # Simular emissão
  nfse danfse <chave_acesso>                     # Baixar DANFSe
  nfse importar <chave_acesso>                   # Importar dados de NFS-e

Para mais informações sobre cada comando, use:
  nfse <comando> --help
        """
    )
    
    # Argumentos globais
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Exibe informações detalhadas de debug (tem precedência sobre --silent)'
    )
    
    parser.add_argument(
        '--silent', '-s',
        action='store_true',
        help='Suprime mensagens informativas, exibindo apenas erros críticos'
    )
    
    # Criar subparsers para comandos
    subparsers = parser.add_subparsers(
        dest='command',
        title='Comandos disponíveis',
        description='Use "nfse <comando> --help" para mais informações sobre cada comando',
        metavar='<comando>'
    )
    
    # Configurar subparser para cada comando
    _configurar_subparser_init(subparsers)
    _configurar_subparser_emitir(subparsers)
    _configurar_subparser_danfse(subparsers)
    _configurar_subparser_importar(subparsers)
    
    return parser


def _configurar_subparser_init(subparsers):
    """
    Configura o subparser para o comando 'init'.
    
    O comando init não possui parâmetros obrigatórios.
    Ele cria a estrutura de diretórios e opcionalmente coleta dados iniciais.
    
    Requisitos: 1.1
    """
    parser_init = subparsers.add_parser(
        'init',
        help='Inicializa estrutura de diretórios e configuração',
        description="""
Inicializa a estrutura de diretórios necessária para o funcionamento do sistema
e opcionalmente coleta dados iniciais da empresa e serviços.

Este comando cria os seguintes diretórios:
  - cert/        : Certificados digitais
  - logs/        : Logs de operações
  - prestadores/ : Arquivos JSON de prestadores
  - tomadores/   : Arquivos JSON de tomadores
  - servicos/    : Arquivos JSON de serviços
  - danfse/      : PDFs de DANFSe baixados
  - nfse/        : XMLs de NFS-e emitidas
  - dps/         : XMLs de DPS enviadas

Após criar os diretórios, o comando oferece a opção de:
  1. Inserir dados da empresa (prestador)
  2. Inserir dados do serviço principal
  3. Definir arquivos padrão no config.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Comando init não tem parâmetros obrigatórios


def _configurar_subparser_emitir(subparsers):
    """
    Configura o subparser para o comando 'emitir'.
    
    Parâmetros obrigatórios:
        --valor: Valor monetário do serviço
        --data: Data/hora de emissão (ISO 8601)
    
    Parâmetros opcionais:
        --ambiente: Ambiente da API (producao ou producaorestrita)
        --dry-run: Modo de simulação
        --prestador: Caminho do arquivo JSON do prestador
        --tomador: Caminho do arquivo JSON do tomador
        --servico: Caminho do arquivo JSON do serviço
    
    Requisitos: 5.1, 5.2, 5.3, 5.4, 6.3, 6.6, 17.1
    """
    parser_emitir = subparsers.add_parser(
        'emitir',
        help='Emite uma NFS-e',
        description="""
Emite uma Nota Fiscal de Serviço Eletrônica (NFS-e) através da API oficial
do Sistema Nacional de NFS-e.

O comando executa as seguintes etapas:
  1. Carrega configuração e certificado digital
  2. Valida dados de entrada
  3. Constrói e assina o XML da DPS
  4. Envia para a API (ou simula em modo dry-run)
  5. Salva arquivos (DPS, NFS-e, log)

Em modo dry-run, todas as etapas são executadas exceto o envio real para a API.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Parâmetros obrigatórios
    parser_emitir.add_argument(
        '--valor',
        type=float,
        required=True,
        help='Valor monetário do serviço (obrigatório). Exemplo: 1500.00'
    )
    
    parser_emitir.add_argument(
        '--data',
        type=str,
        required=True,
        help='Data de emissão. Formatos aceitos: YYYY-MM-DD ou DD/MM/YYYY. '
             'Obrigatório. Exemplos: 2024-01-15 ou 15/01/2024'
    )
    
    # Parâmetros opcionais
    parser_emitir.add_argument(
        '--ambiente',
        type=str,
        choices=['producao', 'producaorestrita'],
        help='Ambiente da API. Sobrescreve o valor do config.json para esta execução. '
             'Valores: producao, producaorestrita'
    )
    
    parser_emitir.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo de simulação. Executa todas as operações exceto o envio real para a API. '
             'Sobrescreve o valor do config.json para esta execução.'
    )
    
    parser_emitir.add_argument(
        '--prestador',
        type=str,
        help='Caminho do arquivo JSON do prestador. Aceita caminhos relativos com subdiretórios. '
             'Se não fornecido, usa o padrão do config.json. '
             'Exemplo: prestadores/empresa_a/prestador.json'
    )
    
    parser_emitir.add_argument(
        '--tomador',
        type=str,
        help='Caminho do arquivo JSON do tomador. Aceita caminhos relativos com subdiretórios. '
             'Se não fornecido, usa o padrão do config.json. '
             'Exemplo: tomadores/clientes/cliente_especial.json'
    )
    
    parser_emitir.add_argument(
        '--servico',
        type=str,
        help='Caminho do arquivo JSON do serviço. Aceita caminhos relativos com subdiretórios. '
             'Se não fornecido, usa o padrão do config.json. '
             'Exemplo: servicos/consultoria/servico_010101.json'
    )


def _configurar_subparser_danfse(subparsers):
    """
    Configura o subparser para o comando 'danfse'.
    
    Parâmetro obrigatório:
        chave_acesso: Chave de acesso da NFS-e (posicional)
    
    Requisitos: 8.1
    """
    parser_danfse = subparsers.add_parser(
        'danfse',
        help='Baixa o PDF (DANFSe) de uma NFS-e',
        description="""
Baixa o Documento Auxiliar da Nota Fiscal de Serviço Eletrônica (DANFSe)
em formato PDF através da API oficial.

O DANFSe é a representação gráfica simplificada da NFS-e, utilizada para
visualização e impressão.

Este comando NÃO gera arquivo de log, apenas salva o PDF no diretório danfse/.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Parâmetro posicional obrigatório
    parser_danfse.add_argument(
        'chave_acesso',
        type=str,
        help='Chave de acesso da NFS-e (50 dígitos). '
             'Exemplo: 35503082123456780001900001000000000000001234567890'
    )


def _configurar_subparser_importar(subparsers):
    """
    Configura o subparser para o comando 'importar'.
    
    Parâmetro obrigatório:
        chave_acesso: Chave de acesso da NFS-e (posicional)
    
    Requisitos: 9.1
    """
    parser_importar = subparsers.add_parser(
        'importar',
        help='Importa dados de uma NFS-e existente',
        description="""
Importa dados de uma NFS-e existente usando sua chave de acesso.

O comando consulta a API, obtém o XML da NFS-e, e extrai os dados para criar
arquivos JSON de template:
  - prestadores/prestador_{timestamp}.json
  - tomadores/tomador_{timestamp}.json
  - servicos/servico_{timestamp}.json

Estes arquivos podem ser usados como base para futuras emissões.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Parâmetro posicional obrigatório
    parser_importar.add_argument(
        'chave_acesso',
        type=str,
        help='Chave de acesso da NFS-e (50 dígitos). '
             'Exemplo: 35503082123456780001900001000000000000001234567890'
    )


def configurar_output(args):
    """
    Configura o modo de output (verbose/silent) baseado nos argumentos.
    
    Regras:
        - Se --verbose é fornecido, ativa modo verbose (tem precedência)
        - Se --silent é fornecido (e não --verbose), ativa modo silencioso
        - Por padrão, modo normal (nem verbose nem silent)
    
    O modo verbose tem precedência sobre o modo silencioso conforme Requisito 19.7.
    
    Args:
        args: Namespace com argumentos parseados
    
    Requisitos: 7.7, 19.7
    """
    global VERBOSE, SILENT
    
    # Verbose tem precedência sobre silent
    if args.verbose:
        VERBOSE = True
        SILENT = False
    elif args.silent:
        VERBOSE = False
        SILENT = True
    else:
        VERBOSE = False
        SILENT = False


def main(argv: Optional[list] = None):
    """
    Entry point principal da aplicação CLI.
    
    Fluxo:
        1. Parseia argumentos da linha de comando
        2. Configura modo de output (verbose/silent)
        3. Executa o comando apropriado
        4. Captura exceções e retorna códigos de saída apropriados
    
    Códigos de saída:
        0: Sucesso
        1: Erro de validação
        2: Erro de certificado
        3: Erro de API
        4: Erro de arquivo
        5: Erro desconhecido
    
    Args:
        argv: Lista de argumentos (para testes). Se None, usa sys.argv[1:]
    
    Returns:
        Código de saída (int)
    
    Requisitos: 11.6
    """
    parser = criar_parser()
    
    # Se nenhum argumento foi fornecido, exibir help
    if argv is None:
        argv = sys.argv[1:]
    
    if len(argv) == 0:
        parser.print_help()
        return 0
    
    # Parsear argumentos
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse chama sys.exit() em caso de erro
        return e.code if e.code is not None else 1
    
    # Configurar modo de output
    configurar_output(args)
    
    # Verificar se um comando foi fornecido
    if not args.command:
        parser.print_help()
        return 0
    
    # Executar comando apropriado
    try:
        if args.command == 'init':
            return executar_init(args)
        elif args.command == 'emitir':
            return executar_emitir(args)
        elif args.command == 'danfse':
            return executar_danfse(args)
        elif args.command == 'importar':
            return executar_importar(args)
        else:
            print(f"❌ Comando desconhecido: {args.command}")
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
        return 130  # Código padrão para SIGINT
    
    except Exception as e:
        # Capturar exceções não tratadas
        if VERBOSE:
            import traceback
            print(f"\n❌ Erro inesperado:")
            traceback.print_exc()
        else:
            print(f"\n❌ Erro inesperado: {str(e)}")
            print("   Use --verbose para mais detalhes")
        return 5


def executar_init(args):
    """
    Executa o comando 'init'.
    
    Cria estrutura de diretórios e coleta dados iniciais de forma interativa.
    
    Args:
        args: Namespace com argumentos parseados
    
    Returns:
        Código de saída (0 = sucesso, != 0 = erro)
    """
    from nfse_core.file_manager import FileManager
    from nfse_core.config import Config
    from nfse_core.models import Prestador, RegimeTributario, Servico
    from nfse_core.validation import validar_cnpj, validar_cpf, validar_codigo_municipio, validar_codigo_tributacao
    
    silent = getattr(args, 'silent', False)
    arquivos_criados = []
    
    try:
        # 1. Criar todos os diretórios necessários
        if not silent:
            print("\n🚀 Inicializando estrutura do nfse-cli...\n")
        
        FileManager.criar_diretorios(silent=silent)
        
        # 2. Carregar ou criar config.json
        config_existe = os.path.exists('config.json')
        config = Config.carregar('config.json')
        
        # 3. Perguntar sobre dados da empresa (prestador)
        if not silent:
            print("\n" + "="*60)
            resposta = input("Deseja inserir dados da empresa (prestador)? (s/n): ").strip().lower()
        else:
            resposta = 'n'
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            if not silent:
                print("\n📋 Coletando dados do prestador...\n")
            
            # Coletar tipo de documento
            while True:
                tipo_doc = input("Tipo de documento (1=CNPJ, 2=CPF): ").strip()
                if tipo_doc in ['1', '2']:
                    break
                print("❌ Opção inválida. Digite 1 para CNPJ ou 2 para CPF.")
            
            # Coletar documento
            while True:
                if tipo_doc == '1':
                    documento = input("CNPJ (14 dígitos): ").strip()
                    if validar_cnpj(documento):
                        cnpj = documento
                        cpf = None
                        break
                    print("❌ CNPJ inválido. Deve ter 14 dígitos numéricos com DV válido.")
                else:
                    documento = input("CPF (11 dígitos): ").strip()
                    if validar_cpf(documento):
                        cpf = documento
                        cnpj = None
                        break
                    print("❌ CPF inválido. Deve ter 11 dígitos numéricos com DV válido.")
            
            # Coletar nome
            xNome = input("Nome/Razão Social: ").strip()
            
            # Coletar código do município
            while True:
                cMun = input("Código do município IBGE (7 dígitos): ").strip()
                if validar_codigo_municipio(cMun):
                    break
                print("❌ Código de município inválido. Deve ter exatamente 7 dígitos numéricos.")
            
            # Coletar inscrição municipal (opcional)
            IM = input("Inscrição Municipal (opcional, Enter para pular): ").strip()
            if not IM:
                IM = None
            
            # Coletar email (opcional)
            email = input("Email (opcional, Enter para pular): ").strip()
            if not email:
                email = None
            
            # Coletar dados do regime tributário
            if not silent:
                print("\n📊 Regime Tributário:\n")
            
            while True:
                print("Opção pelo Simples Nacional:")
                print("  1 = Não Optante")
                print("  2 = MEI")
                print("  3 = ME/EPP")
                opSimpNac = input("Digite a opção (1, 2 ou 3): ").strip()
                if opSimpNac in ['1', '2', '3']:
                    opSimpNac = int(opSimpNac)
                    break
                print("❌ Opção inválida. Digite 1, 2 ou 3.")
            
            while True:
                print("\nRegime Especial de Tributação:")
                print("  0 = Nenhum")
                print("  1-6 ou 9 = Outros regimes especiais")
                regEspTrib = input("Digite a opção (0-6 ou 9): ").strip()
                if regEspTrib in ['0', '1', '2', '3', '4', '5', '6', '9']:
                    regEspTrib = int(regEspTrib)
                    break
                print("❌ Opção inválida. Digite 0, 1-6 ou 9.")
            
            # Coletar regApTribSN apenas se opSimpNac = 3
            regApTribSN = None
            if opSimpNac == 3:
                while True:
                    print("\nRegime de Apuração (apenas para ME/EPP):")
                    print("  1, 2 ou 3")
                    regApTribSN_input = input("Digite a opção (1, 2 ou 3): ").strip()
                    if regApTribSN_input in ['1', '2', '3']:
                        regApTribSN = int(regApTribSN_input)
                        break
                    print("❌ Opção inválida. Digite 1, 2 ou 3.")
            
            # Criar objeto RegimeTributario
            regTrib = RegimeTributario(
                opSimpNac=opSimpNac,
                regEspTrib=regEspTrib,
                regApTribSN=regApTribSN
            )
            
            # Criar objeto Prestador
            prestador = Prestador(
                CNPJ=cnpj,
                CPF=cpf,
                xNome=xNome,
                cMun=cMun,
                IM=IM,
                email=email,
                regTrib=regTrib
            )
            
            # Validar dados
            erros = prestador.validar()
            if erros:
                print("\n❌ Erros de validação:")
                for erro in erros:
                    print(f"   - {erro}")
                return 1
            
            # Salvar arquivo prestador
            doc_prestador = cnpj if cnpj else cpf
            nome_arquivo_prestador = f"prestador_{doc_prestador}.json"
            caminho_prestador = os.path.join('prestadores', nome_arquivo_prestador)
            prestador.salvar(caminho_prestador)
            arquivos_criados.append(caminho_prestador)
            
            if not silent:
                print(f"\n✓ Arquivo do prestador salvo: {caminho_prestador}")
            
            # Perguntar se deseja definir como padrão
            if not silent:
                resposta_padrao = input("\nDeseja definir este prestador como padrão? (s/n): ").strip().lower()
            else:
                resposta_padrao = 'n'
            
            if resposta_padrao in ['s', 'sim', 'y', 'yes']:
                config.atualizar_default('prestador', caminho_prestador)
                if not silent:
                    print("✓ Prestador definido como padrão no config.json")
        
        # 4. Perguntar sobre dados do serviço
        if not silent:
            print("\n" + "="*60)
            resposta_servico = input("Deseja inserir dados do serviço principal? (s/n): ").strip().lower()
        else:
            resposta_servico = 'n'
        
        if resposta_servico in ['s', 'sim', 'y', 'yes']:
            if not silent:
                print("\n📋 Coletando dados do serviço...\n")
            
            # Coletar descrição do serviço
            xDescServ = input("Descrição do serviço: ").strip()
            
            # Coletar código de tributação nacional
            while True:
                cTribNac = input("Código de Tributação Nacional (6 dígitos numéricos): ").strip()
                if validar_codigo_tributacao(cTribNac):
                    break
                print("❌ Código de tributação inválido. Deve ter exatamente 6 dígitos numéricos.")
            
            # Coletar código do município onde o serviço é prestado
            while True:
                cLocPrestacao = input("Código do município onde o serviço é prestado (7 dígitos): ").strip()
                if validar_codigo_municipio(cLocPrestacao):
                    break
                print("❌ Código de município inválido. Deve ter exatamente 7 dígitos numéricos.")
            
            # Coletar código de tributação municipal (opcional)
            cTribMun = input("Código de Tributação Municipal (3 dígitos, opcional, Enter para pular): ").strip()
            if not cTribMun:
                cTribMun = None
            
            # Coletar código NBS (opcional)
            cNBS = input("Código NBS (opcional, Enter para pular): ").strip()
            if not cNBS:
                cNBS = None
            
            # Criar objeto Servico
            servico = Servico(
                xDescServ=xDescServ,
                cTribNac=cTribNac,
                cLocPrestacao=cLocPrestacao,
                cTribMun=cTribMun,
                cNBS=cNBS
            )
            
            # Validar dados
            erros_servico = servico.validar()
            if erros_servico:
                print("\n❌ Erros de validação:")
                for erro in erros_servico:
                    print(f"   - {erro}")
                return 1
            
            # Salvar arquivo serviço (remover pontos do código)
            codigo_limpo = cTribNac.replace('.', '')
            nome_arquivo_servico = f"servico_{codigo_limpo}.json"
            caminho_servico = os.path.join('servicos', nome_arquivo_servico)
            servico.salvar(caminho_servico)
            arquivos_criados.append(caminho_servico)
            
            if not silent:
                print(f"\n✓ Arquivo do serviço salvo: {caminho_servico}")
            
            # Perguntar se deseja definir como padrão
            if not silent:
                resposta_padrao_servico = input("\nDeseja definir este serviço como padrão? (s/n): ").strip().lower()
            else:
                resposta_padrao_servico = 'n'
            
            if resposta_padrao_servico in ['s', 'sim', 'y', 'yes']:
                config.atualizar_default('servicos', caminho_servico)
                if not silent:
                    print("✓ Serviço definido como padrão no config.json")
        
        # 5. Salvar config.json
        config.salvar('config.json')
        if not config_existe:
            arquivos_criados.append('config.json')
            if not silent:
                print("\n✓ Arquivo de configuração criado: config.json")
        else:
            if not silent:
                print("\n✓ Arquivo de configuração atualizado: config.json")
        
        # 6. Exibir mensagem de sucesso
        if not silent:
            print("\n" + "="*60)
            print("✅ Inicialização concluída com sucesso!\n")
            
            if arquivos_criados:
                print("📁 Arquivos criados:")
                for arquivo in arquivos_criados:
                    print(f"   - {arquivo}")
            
            print("\n💡 Próximos passos:")
            print("   1. Configure seu certificado digital em cert/")
            print("   2. Use 'python nfse.py emitir --valor <valor> --data <data>' para emitir uma nota")
            print("   3. Use 'python nfse.py --help' para ver todos os comandos disponíveis")
            print()
        
        return 0
        
    except KeyboardInterrupt:
        if not silent:
            print("\n\n⚠️  Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro durante inicialização: {e}")
        return 1


def executar_emitir(args):
    """
    Executa o comando 'emitir'.
    
    Fluxo completo de emissão de NFS-e:
    1. Carregar configuração
    2. Validar parâmetros obrigatórios
    3. Validar certificado digital
    4. Carregar dados de prestador, tomador e serviço
    5. Validar dados
    6. Gerar ID do DPS
    7. Construir XML do DPS
    8. Assinar XML
    9. Salvar DPS
    10. Comprimir XML
    11. Enviar para API (ou simular se dry_run)
    12. Processar resposta
    13. Salvar NFS-e e log
    
    Args:
        args: Namespace com argumentos parseados
    
    Returns:
        Código de saída (0 = sucesso, != 0 = erro)
    """
    from .config import Config
    from .models import Prestador, Tomador, Servico
    from .validation import (
        validar_valor, validar_data_iso, converter_data_para_iso8601,
        validar_cnpj, validar_cpf, validar_codigo_municipio, validar_codigo_tributacao,
        validar_local_incidencia, validar_obrigatoriedade_ibscbs, ValidationError
    )
    from .crypto import (
        carregar_pfx, validar_certificado, assinar_xml, comprimir_xml,
        CertificateError
    )
    from .xml_builder import gerar_id_dps, construir_xml_dps, xml_para_string
    from .api_client import APIClient
    from .file_manager import FileManager
    from .logger import criar_log_emissao
    
    try:
        # === 1. Carregar config.json ===
        if not SILENT:
            print("📋 Carregando configuração...")
        
        try:
            config = Config.carregar()
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return 4
        
        # Aplicar overrides de ambiente e dry_run se fornecidos via CLI
        if args.ambiente:
            config.ambiente = args.ambiente
            if not SILENT:
                print(f"   Ambiente sobrescrito via CLI: {config.ambiente}")
        
        if args.dry_run is not None:
            config.dry_run = args.dry_run
            if not SILENT:
                print(f"   Modo dry-run sobrescrito via CLI: {config.dry_run}")
        
        if config.dry_run and not SILENT:
            print("⚠️  Modo DRY-RUN ativo: Nenhuma requisição real será enviada para a API")
        
        # === 2. Validar parâmetros obrigatórios ===
        if not SILENT:
            print("✓ Validando parâmetros...")
        
        # Validar --valor
        if args.valor is None:
            print("❌ Erro de Validação: Parâmetro --valor é obrigatório")
            return 1
        
        # Validar --data
        if args.data is None:
            print("❌ Erro de Validação: Parâmetro --data é obrigatório")
            return 1
        
        # Validar formato de data
        try:
            validar_data_iso(args.data)
            # Converter data para formato ISO 8601 com hora
            data_emissao_iso = converter_data_para_iso8601(args.data)
        except ValidationError as e:
            print(f"❌ Erro de Validação: {e}")
            return 1
        
        # Validar valor positivo
        try:
            validar_valor(args.valor)
        except ValidationError as e:
            print(f"❌ Erro de Validação: {e}")
            return 1
        
        # === 3. Carregar e validar certificado digital ===
        if not SILENT:
            print("🔐 Carregando certificado digital...")
        
        # Verificar se arquivo de certificado existe
        if not os.path.exists(config.arquivo_pfx):
            print(f"❌ Erro de Certificado: Arquivo não encontrado: {config.arquivo_pfx}")
            return 2
        
        # Verificar se arquivo de senha existe
        if not os.path.exists(config.arquivo_senha_cert):
            print(f"❌ Erro de Certificado: Arquivo de senha não encontrado: {config.arquivo_senha_cert}")
            return 2
        
        # Ler senha do certificado
        try:
            with open(config.arquivo_senha_cert, 'r', encoding='utf-8') as f:
                senha_cert = f.read().strip()
        except Exception as e:
            print(f"❌ Erro ao ler senha do certificado: {e}")
            return 2
        
        # Validar certificado
        try:
            cert_info = validar_certificado(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro de Certificado: {e}")
            return 2
        
        # Exibir informações do certificado (exceto em modo silencioso)
        if not SILENT:
            print(f"✓ Certificado válido:")
            print(f"   Titular: {cert_info.titular}")
            print(f"   Emissor: {cert_info.emissor}")
            print(f"   Validade: {cert_info.validade_inicio.strftime('%d/%m/%Y')} até {cert_info.validade_fim.strftime('%d/%m/%Y')}")
            print(f"   Dias para expirar: {cert_info.dias_para_expirar}")
            
            # Aviso se certificado expira em menos de 30 dias
            if cert_info.dias_para_expirar < 30:
                print(f"⚠️  AVISO: Certificado expira em menos de 30 dias!")
        
        # Carregar certificado em formato PEM
        try:
            pem_data = carregar_pfx(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro ao carregar certificado: {e}")
            return 2
        
        # === 4. Carregar arquivos JSON de prestador, tomador e serviço ===
        if not SILENT:
            print("📂 Carregando dados...")
        
        # Determinar caminho do prestador
        caminho_prestador = args.prestador if args.prestador else config.defaults.get('prestador')
        if not caminho_prestador:
            print("❌ Erro: Caminho do prestador não fornecido. Use --prestador ou configure um padrão.")
            return 1
        
        # Determinar caminho do tomador
        caminho_tomador = args.tomador if args.tomador else config.defaults.get('tomador')
        if not caminho_tomador:
            print("❌ Erro: Caminho do tomador não fornecido. Use --tomador ou configure um padrão.")
            return 1
        
        # Determinar caminho do serviço
        caminho_servico = args.servico if args.servico else config.defaults.get('servicos')
        if not caminho_servico:
            print("❌ Erro: Caminho do serviço não fornecido. Use --servico ou configure um padrão.")
            return 1
        
        # Carregar prestador
        try:
            prestador = Prestador.carregar(caminho_prestador)
            if not SILENT:
                print(f"✓ Prestador carregado: {caminho_prestador}")
        except FileNotFoundError as e:
            print(f"❌ Erro de Arquivo: {e}")
            return 4
        except Exception as e:
            print(f"❌ Erro ao carregar prestador: {e}")
            return 4
        
        # Carregar tomador
        try:
            tomador = Tomador.carregar(caminho_tomador)
            if not SILENT:
                print(f"✓ Tomador carregado: {caminho_tomador}")
        except FileNotFoundError as e:
            print(f"❌ Erro de Arquivo: {e}")
            return 4
        except Exception as e:
            print(f"❌ Erro ao carregar tomador: {e}")
            return 4
        
        # Carregar serviço
        try:
            servico = Servico.carregar(caminho_servico)
            if not SILENT:
                print(f"✓ Serviço carregado: {caminho_servico}")
        except FileNotFoundError as e:
            print(f"❌ Erro de Arquivo: {e}")
            return 4
        except Exception as e:
            print(f"❌ Erro ao carregar serviço: {e}")
            return 4
        
        # === 5. Validar dados de prestador, tomador e serviço ===
        if not SILENT:
            print("✓ Validando dados...")
        
        # Validar prestador
        erros_prestador = prestador.validar()
        if erros_prestador:
            print(f"❌ Erro de Validação no prestador ({caminho_prestador}):")
            for erro in erros_prestador:
                print(f"   - {erro}")
            return 1
        
        # Validar documento do prestador (CNPJ ou CPF com DV)
        try:
            if prestador.CNPJ:
                validar_cnpj(prestador.CNPJ)
            else:
                validar_cpf(prestador.CPF)
        except ValidationError as e:
            print(f"❌ Erro de Validação no prestador: {e}")
            return 1
        
        # Validar tomador
        erros_tomador = tomador.validar()
        if erros_tomador:
            print(f"❌ Erro de Validação no tomador ({caminho_tomador}):")
            for erro in erros_tomador:
                print(f"   - {erro}")
            return 1
        
        # Validar documento do tomador (CNPJ ou CPF com DV)
        try:
            if tomador.CNPJ:
                validar_cnpj(tomador.CNPJ)
            else:
                validar_cpf(tomador.CPF)
        except ValidationError as e:
            print(f"❌ Erro de Validação no tomador: {e}")
            return 1
        
        # Validar serviço
        erros_servico = servico.validar()
        if erros_servico:
            print(f"❌ Erro de Validação no serviço ({caminho_servico}):")
            for erro in erros_servico:
                print(f"   - {erro}")
            return 1
        
        # Validar código de tributação
        try:
            validar_codigo_tributacao(servico.cTribNac)
        except ValidationError as e:
            print(f"❌ Erro de Validação no serviço: {e}")
            return 1
        
        # Validar regras de incidência do ISSQN
        # Para simplificar, assumimos que cLocIncid = cLocPrestacao (pode ser ajustado conforme regras)
        try:
            c_loc_incid = servico.cLocPrestacao
            validar_local_incidencia(
                servico.cTribNac,
                c_loc_incid,
                servico.cLocPrestacao,
                prestador.cMun,
                tomador.end.cMun if tomador.end else prestador.cMun
            )
        except ValidationError as e:
            print(f"❌ Erro de Validação: {e}")
            return 1
        
        # Validar obrigatoriedade do grupo IBSCBS
        try:
            # Extrair data de competência da data de emissão (formato YYYY-MM-DD)
            data_competencia = data_emissao_iso.split('T')[0]
            validar_obrigatoriedade_ibscbs(
                prestador.regTrib,
                data_competencia,
                servico.ibscbs is not None
            )
        except ValidationError as e:
            print(f"❌ Erro de Validação: {e}")
            return 1
        
        # === 6. Gerar ID do DPS ===
        if not SILENT:
            print("🔢 Gerando ID do DPS...")
        
        id_dps = gerar_id_dps(prestador, config)
        if not SILENT:
            print(f"✓ ID do DPS: {id_dps}")
        
        # === 7. Construir XML do DPS ===
        if not SILENT:
            print("📝 Construindo XML do DPS...")
        
        xml_dps = construir_xml_dps(
            prestador=prestador,
            tomador=tomador,
            servico=servico,
            valor=args.valor,
            data_emissao=data_emissao_iso,
            id_dps=id_dps,
            config=config
        )
        
        # Exibir XML em modo verbose
        if VERBOSE:
            xml_string = xml_para_string(xml_dps)
            print("📄 XML do DPS gerado:")
            print(xml_string)
        
        # === 8. Assinar XML com certificado ===
        if not SILENT:
            print("✍️  Assinando XML...")
        
        try:
            xml_assinado = assinar_xml(xml_dps, pem_data)
        except CertificateError as e:
            print(f"❌ Erro ao assinar XML: {e}")
            if VERBOSE:
                import traceback
                traceback.print_exc()
            return 2
        
        # === 9. Salvar DPS no diretório dps/ ===
        if not SILENT:
            print("💾 Salvando DPS...")
        
        timestamp = FileManager.gerar_timestamp()
        nome_arquivo_dps = FileManager.gerar_nome_arquivo(
            timestamp,
            prestador.obter_documento(),
            tomador.obter_documento(),
            'xml'
        )
        
        xml_dps_string = xml_para_string(xml_assinado)
        FileManager.salvar_dps(xml_dps_string, nome_arquivo_dps, silent=SILENT)
        
        # === 10. Comprimir XML (Gzip + Base64) ===
        if not SILENT:
            print("🗜️  Comprimindo XML...")
        
        dps_comprimido = comprimir_xml(xml_assinado, verbose=VERBOSE)
        
        # Exibir payload em modo verbose
        if VERBOSE:
            print(f"📦 Payload Base64 (primeiros 100 caracteres):")
            print(f"   {dps_comprimido[:100]}...")
        
        # === 11. Enviar para API (ou simular se dry_run) ===
        if config.dry_run:
            if not SILENT:
                print("🎭 Simulando envio para API (modo dry-run)...")
                print(f"   URL: {config.obter_url_api()}/nfse")
                print(f"   Método: POST")
                print(f"   Tamanho do payload: {len(dps_comprimido)} bytes")
        else:
            if not SILENT:
                print("📡 Enviando para API...")
                print(f"   URL: {config.obter_url_api()}/nfse")
        
        # Usar APIClient com context manager
        try:
            with APIClient(config, pem_data) as api_client:
                resposta = api_client.emitir_nfse(dps_comprimido, dry_run=config.dry_run)
        except Exception as e:
            print(f"❌ Erro ao comunicar com API: {e}")
            if VERBOSE:
                import traceback
                traceback.print_exc()
            return 3
        
        # === 12. Processar resposta da API ===
        if not resposta.sucesso:
            print(f"❌ Erro na API: {resposta.erro}")
            if VERBOSE and resposta.dados:
                print(f"   Dados da resposta: {resposta.dados}")
            
            # Salvar log mesmo em caso de erro
            log = criar_log_emissao(
                config, prestador, tomador, servico,
                args.valor, data_emissao_iso, id_dps, resposta, timestamp
            )
            nome_arquivo_log = FileManager.gerar_nome_arquivo(
                timestamp,
                prestador.obter_documento(),
                tomador.obter_documento(),
                'json'
            )
            FileManager.salvar_log(log.para_dict(), nome_arquivo_log, silent=SILENT)
            
            return 3
        
        # === 13. Salvar NFS-e e log ===
        if not SILENT:
            print("✅ Emissão bem-sucedida!")
        
        # Extrair chave de acesso
        chave_acesso = resposta.dados.get('chaveAcesso', 'N/A')
        
        if not config.dry_run:
            # Salvar NFS-e (descomprimir XML da resposta)
            if 'nfseXmlGZipB64' in resposta.dados:
                from .crypto import descomprimir_xml
                try:
                    xml_nfse = descomprimir_xml(resposta.dados['nfseXmlGZipB64'])
                    nome_arquivo_nfse = FileManager.gerar_nome_arquivo(
                        timestamp,
                        prestador.obter_documento(),
                        tomador.obter_documento(),
                        'xml'
                    )
                    FileManager.salvar_nfse(xml_nfse, nome_arquivo_nfse, silent=SILENT)
                except Exception as e:
                    if not SILENT:
                        print(f"⚠️  Aviso: Não foi possível salvar XML da NFS-e: {e}")
        
        # Salvar log estruturado
        log = criar_log_emissao(
            config, prestador, tomador, servico,
            args.valor, data_emissao_iso, id_dps, resposta, timestamp
        )
        nome_arquivo_log = FileManager.gerar_nome_arquivo(
            timestamp,
            prestador.obter_documento(),
            tomador.obter_documento(),
            'json'
        )
        FileManager.salvar_log(log.para_dict(), nome_arquivo_log, silent=SILENT)
        
        # === 14. Exibir resultado ===
        if not SILENT:
            print()
            print("=" * 60)
            print("📋 RESUMO DA EMISSÃO")
            print("=" * 60)
            print(f"Chave de Acesso: {chave_acesso}")
            print(f"Ambiente: {config.ambiente}")
            print(f"Prestador: {prestador.xNome}")
            print(f"Tomador: {tomador.xNome}")
            print(f"Valor: R$ {args.valor:.2f}")
            print(f"Data de Emissão: {data_emissao_iso}")
            if config.dry_run:
                print(f"Modo: DRY-RUN (simulação)")
            print("=" * 60)
        
        # Incrementar próximo número do DPS no config
        config.proximo_numero += 1
        try:
            config.salvar()
        except Exception as e:
            if not SILENT:
                print(f"⚠️  Aviso: Não foi possível atualizar config.json: {e}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return 1
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        return 1


def executar_danfse(args):
    """
    Executa o comando 'danfse'.
    
    Fluxo de download de DANFSe:
    1. Carregar configuração
    2. Validar e carregar certificado digital
    3. Tentar consultar NFS-e para obter dados do prestador e tomador (opcional)
    4. Fazer requisição GET para /danfse/{chaveAcesso} via mTLS
    5. Salvar PDF no diretório danfse/ com nome padronizado (completo ou simplificado)
    6. Exibir mensagem de sucesso
    
    Se a consulta da NFS-e falhar, o sistema exibe um aviso e continua com o
    download do PDF, salvando com nome simplificado: {timestamp}_{chave_acesso}.pdf
    
    Se a consulta for bem-sucedida, salva com nome completo:
    {timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.pdf
    
    NÃO cria arquivo de log (conforme requisito 8.2).
    
    Args:
        args: Namespace com argumentos parseados
    
    Returns:
        Código de saída (0 = sucesso, != 0 = erro)
    """
    from .config import Config
    from .crypto import carregar_pfx, validar_certificado, descomprimir_xml, CertificateError
    from .api_client import APIClient
    from .file_manager import FileManager
    from lxml import etree
    import requests
    
    try:
        # === 1. Carregar config.json ===
        if not SILENT:
            print("📋 Carregando configuração...")
        
        try:
            config = Config.carregar()
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return 4
        
        # === 2. Validar e carregar certificado digital ===
        if not SILENT:
            print("🔐 Carregando certificado digital...")
        
        # Verificar se arquivo de certificado existe
        if not os.path.exists(config.arquivo_pfx):
            print(f"❌ Erro de Certificado: Arquivo não encontrado: {config.arquivo_pfx}")
            return 2
        
        # Verificar se arquivo de senha existe
        if not os.path.exists(config.arquivo_senha_cert):
            print(f"❌ Erro de Certificado: Arquivo de senha não encontrado: {config.arquivo_senha_cert}")
            return 2
        
        # Ler senha do certificado
        try:
            with open(config.arquivo_senha_cert, 'r', encoding='utf-8') as f:
                senha_cert = f.read().strip()
        except Exception as e:
            print(f"❌ Erro ao ler senha do certificado: {e}")
            return 2
        
        # Validar certificado
        try:
            cert_info = validar_certificado(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro de Certificado: {e}")
            return 2
        
        # Exibir informações do certificado (exceto em modo silencioso)
        if not SILENT:
            print(f"✓ Certificado válido: {cert_info.titular}")
            print(f"   Emissor: {cert_info.emissor}")
            print(f"   Validade: {cert_info.validade_fim.strftime('%d/%m/%Y')}")
            
            # Aviso se certificado expira em menos de 30 dias
            if cert_info.dias_para_expirar < 30:
                print(f"⚠️  Atenção: Certificado expira em {cert_info.dias_para_expirar} dias")
        
        # Carregar certificado em formato PEM
        try:
            pem_data = carregar_pfx(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro ao carregar certificado: {e}")
            return 2
        
        # === 3. Consultar NFS-e para obter dados do prestador e tomador (opcional) ===
        documento_prestador = None
        documento_tomador = None
        
        if not SILENT:
            print(f"🔍 Consultando NFS-e para obter dados: {args.chave_acesso}")
        
        try:
            with APIClient(config, pem_data) as api_client:
                resposta = api_client.consultar_nfse(args.chave_acesso)
            
            # Verificar se a consulta foi bem-sucedida
            if resposta.sucesso and 'nfseXmlGZipB64' in resposta.dados:
                # Descomprimir XML da NFS-e
                try:
                    xml_string = descomprimir_xml(resposta.dados['nfseXmlGZipB64'])
                    
                    # Parsear XML da NFS-e
                    root = etree.fromstring(xml_string.encode('utf-8'))
                    
                    # Namespace do XML (se houver)
                    namespaces = root.nsmap if hasattr(root, 'nsmap') else {}
                    
                    # Função auxiliar para buscar elementos com ou sem namespace
                    def find_element(parent, tag):
                        """Busca elemento com ou sem namespace"""
                        # Tentar sem namespace primeiro
                        elem = parent.find(tag)
                        if elem is not None:
                            return elem
                        
                        # Tentar com namespace padrão
                        if None in namespaces:
                            elem = parent.find(f"{{{namespaces[None]}}}{tag}")
                            if elem is not None:
                                return elem
                        
                        # Tentar com todos os namespaces
                        for ns_prefix, ns_uri in namespaces.items():
                            if ns_prefix is not None:
                                elem = parent.find(f"{{{ns_uri}}}{tag}")
                                if elem is not None:
                                    return elem
                        
                        return None
                    
                    def get_text(parent, tag, default=""):
                        """Obtém texto de um elemento, retorna default se não encontrado"""
                        elem = find_element(parent, tag)
                        return elem.text if elem is not None and elem.text else default
                    
                    # Extrair CNPJ do prestador e documento do tomador
                    inf_nfse = find_element(root, 'infNFSe')
                    if inf_nfse is None:
                        inf_nfse = find_element(root, 'infDPS')
                    
                    if inf_nfse is not None:
                        # Extrair CNPJ do prestador
                        prest_elem = find_element(inf_nfse, 'prest')
                        if prest_elem is not None:
                            cnpj_prestador = get_text(prest_elem, 'CNPJ')
                            cpf_prestador = get_text(prest_elem, 'CPF')
                            documento_prestador = cnpj_prestador if cnpj_prestador else cpf_prestador
                        
                        # Extrair documento do tomador
                        toma_elem = find_element(inf_nfse, 'toma')
                        if toma_elem is not None:
                            cnpj_tomador = get_text(toma_elem, 'CNPJ')
                            cpf_tomador = get_text(toma_elem, 'CPF')
                            documento_tomador = cnpj_tomador if cnpj_tomador else cpf_tomador
                    
                    if documento_prestador and documento_tomador:
                        if not SILENT:
                            print(f"✓ Dados extraídos: Prestador {documento_prestador}, Tomador {documento_tomador}")
                    else:
                        if not SILENT:
                            print("⚠️  Não foi possível extrair todos os dados da NFS-e")
                            print("   O arquivo será salvo com nome simplificado")
                
                except Exception as e:
                    if not SILENT:
                        print(f"⚠️  Erro ao processar XML da NFS-e: {e}")
                        print("   O arquivo será salvo com nome simplificado")
                    if VERBOSE:
                        import traceback
                        traceback.print_exc()
            else:
                if not SILENT:
                    print(f"⚠️  Não foi possível consultar NFS-e: {resposta.erro if not resposta.sucesso else 'XML não encontrado na resposta'}")
                    print("   O arquivo será salvo com nome simplificado")
        
        except Exception as e:
            if not SILENT:
                print(f"⚠️  Erro ao consultar NFS-e: {e}")
                print("   O arquivo será salvo com nome simplificado")
            if VERBOSE:
                import traceback
                traceback.print_exc()
        
        # === 4. Fazer requisição GET para /danfse/{chaveAcesso} via mTLS ===
        if not SILENT:
            print(f"📥 Baixando DANFSe...")
        
        try:
            with APIClient(config, pem_data) as api_client:
                pdf_bytes = api_client.baixar_danfse(args.chave_acesso)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de API: {e}")
            return 3
        except ValueError as e:
            print(f"❌ Erro: {e}")
            return 3
        except Exception as e:
            print(f"❌ Erro inesperado ao baixar DANFSe: {e}")
            if VERBOSE:
                import traceback
                traceback.print_exc()
            return 3
        
        # === 5. Salvar PDF no diretório danfse/ ===
        # Gerar nome do arquivo baseado nos dados disponíveis
        timestamp = FileManager.gerar_timestamp()
        
        if documento_prestador and documento_tomador:
            # Formato completo: {timestamp}_{cnpj_prestador}_{documento_tomador}_{chave_acesso}.pdf
            nome_arquivo = f"{timestamp}_{documento_prestador}_{documento_tomador}_{args.chave_acesso}.pdf"
        else:
            # Formato simplificado: {timestamp}_{chave_acesso}.pdf
            nome_arquivo = f"{timestamp}_{args.chave_acesso}.pdf"
        
        try:
            FileManager.salvar_danfse(pdf_bytes, nome_arquivo, silent=SILENT)
        except Exception as e:
            print(f"❌ Erro ao salvar DANFSe: {e}")
            return 4
        
        # === 6. Exibir mensagem de sucesso ===
        if not SILENT:
            caminho_completo = os.path.join('danfse', nome_arquivo)
            print(f"✅ DANFSe baixado com sucesso!")
            print(f"   Arquivo salvo: {caminho_completo}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        return 1


def executar_importar(args):
    """
    Executa o comando 'importar'.
    
    Fluxo de importação de NFS-e:
    1. Carregar configuração
    2. Validar e carregar certificado digital
    3. Fazer requisição GET para /nfse/{chaveAcesso} via mTLS
    4. Descomprimir XML da NFS-e (Base64 + Gzip)
    5. Parsear XML da NFS-e
    6. Extrair dados do prestador e salvar em prestadores/prestador_{timestamp}.json
    7. Extrair dados do tomador e salvar em tomadores/tomador_{timestamp}.json
    8. Extrair dados do serviço e salvar em servicos/servico_{timestamp}.json
    9. Exibir mensagens informativas com caminhos dos arquivos criados
    
    Args:
        args: Namespace com argumentos parseados
    
    Returns:
        Código de saída (0 = sucesso, != 0 = erro)
    """
    from .config import Config
    from .crypto import carregar_pfx, validar_certificado, descomprimir_xml, CertificateError
    from .api_client import APIClient
    from .file_manager import FileManager
    from .models import Prestador, Tomador, Servico, Endereco, RegimeTributario
    from lxml import etree
    
    try:
        # === 1. Carregar config.json ===
        if not SILENT:
            print("📋 Carregando configuração...")
        
        try:
            config = Config.carregar()
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return 4
        
        # === 2. Validar e carregar certificado digital ===
        if not SILENT:
            print("🔐 Carregando certificado digital...")
        
        # Verificar se arquivo de certificado existe
        if not os.path.exists(config.arquivo_pfx):
            print(f"❌ Erro de Certificado: Arquivo não encontrado: {config.arquivo_pfx}")
            return 2
        
        # Verificar se arquivo de senha existe
        if not os.path.exists(config.arquivo_senha_cert):
            print(f"❌ Erro de Certificado: Arquivo de senha não encontrado: {config.arquivo_senha_cert}")
            return 2
        
        # Ler senha do certificado
        try:
            with open(config.arquivo_senha_cert, 'r', encoding='utf-8') as f:
                senha_cert = f.read().strip()
        except Exception as e:
            print(f"❌ Erro ao ler senha do certificado: {e}")
            return 2
        
        # Validar certificado
        try:
            cert_info = validar_certificado(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro de Certificado: {e}")
            return 2
        
        # Exibir informações do certificado (exceto em modo silencioso)
        if not SILENT:
            print(f"✓ Certificado válido: {cert_info.titular}")
            print(f"   Emissor: {cert_info.emissor}")
            print(f"   Validade: {cert_info.validade_fim.strftime('%d/%m/%Y')}")
            
            # Aviso se certificado expira em menos de 30 dias
            if cert_info.dias_para_expirar < 30:
                print(f"⚠️  Atenção: Certificado expira em {cert_info.dias_para_expirar} dias")
        
        # Carregar certificado em formato PEM
        try:
            pem_data = carregar_pfx(config.arquivo_pfx, senha_cert)
        except CertificateError as e:
            print(f"❌ Erro ao carregar certificado: {e}")
            return 2
        
        # === 3. Fazer requisição GET para /nfse/{chaveAcesso} via mTLS ===
        if not SILENT:
            print(f"📥 Consultando NFS-e com chave de acesso: {args.chave_acesso}")
        
        try:
            with APIClient(config, pem_data) as api_client:
                resposta = api_client.consultar_nfse(args.chave_acesso)
        except Exception as e:
            print(f"❌ Erro inesperado ao consultar NFS-e: {e}")
            if VERBOSE:
                import traceback
                traceback.print_exc()
            return 3
        
        # Verificar se a consulta foi bem-sucedida
        if not resposta.sucesso:
            print(f"❌ Erro de API: {resposta.erro}")
            return 3
        
        # Verificar se a resposta contém o XML da NFS-e
        if 'nfseXmlGZipB64' not in resposta.dados:
            print("❌ Erro: Resposta da API não contém o XML da NFS-e")
            return 3
        
        # === 4. Descomprimir XML da NFS-e (Base64 + Gzip) ===
        if not SILENT:
            print("📦 Descomprimindo XML da NFS-e...")
        
        try:
            xml_string = descomprimir_xml(resposta.dados['nfseXmlGZipB64'])
        except ValueError as e:
            print(f"❌ Erro ao descomprimir XML: {e}")
            return 3
        
        # === 5. Parsear XML da NFS-e ===
        if not SILENT:
            print("🔍 Parseando XML da NFS-e...")
        
        try:
            root = etree.fromstring(xml_string.encode('utf-8'))
        except Exception as e:
            print(f"❌ Erro ao parsear XML: {e}")
            if VERBOSE:
                print(f"   XML recebido: {xml_string[:500]}...")
            return 3
        
        # Namespace do XML (se houver)
        namespaces = root.nsmap if hasattr(root, 'nsmap') else {}
        
        # Função auxiliar para buscar elementos com ou sem namespace
        def find_element(parent, tag):
            """Busca elemento com ou sem namespace"""
            # Tentar sem namespace primeiro
            elem = parent.find(tag)
            if elem is not None:
                return elem
            
            # Tentar com namespace padrão
            if None in namespaces:
                elem = parent.find(f"{{{namespaces[None]}}}{tag}")
                if elem is not None:
                    return elem
            
            # Tentar com todos os namespaces
            for ns_prefix, ns_uri in namespaces.items():
                if ns_prefix is not None:
                    elem = parent.find(f"{{{ns_uri}}}{tag}")
                    if elem is not None:
                        return elem
            
            return None
        
        def get_text(parent, tag, default=""):
            """Obtém texto de um elemento, retorna default se não encontrado"""
            elem = find_element(parent, tag)
            return elem.text if elem is not None and elem.text else default
        
        # === 6. Extrair dados do prestador ===
        if not SILENT:
            print("👤 Extraindo dados do prestador...")
        
        # Buscar elemento do prestador (pode estar em infNFSe/prest ou DPS/infDPS/prest)
        inf_nfse = find_element(root, 'infNFSe')
        if inf_nfse is None:
            inf_nfse = find_element(root, 'infDPS')
        
        if inf_nfse is None:
            print("❌ Erro: Não foi possível encontrar elemento infNFSe ou infDPS no XML")
            return 3
        
        prest_elem = find_element(inf_nfse, 'prest')
        if prest_elem is None:
            print("❌ Erro: Não foi possível encontrar elemento 'prest' no XML")
            return 3
        
        # Extrair dados do prestador
        prestador_data = {}
        
        # CNPJ ou CPF
        cnpj = get_text(prest_elem, 'CNPJ')
        cpf = get_text(prest_elem, 'CPF')
        if cnpj:
            prestador_data['CNPJ'] = cnpj
        elif cpf:
            prestador_data['CPF'] = cpf
        
        prestador_data['xNome'] = get_text(prest_elem, 'xNome')
        prestador_data['cMun'] = get_text(prest_elem, 'cMun')
        prestador_data['IM'] = get_text(prest_elem, 'IM') or None
        prestador_data['email'] = get_text(prest_elem, 'email') or None
        
        # Extrair regime tributário
        reg_trib_elem = find_element(prest_elem, 'regTrib')
        if reg_trib_elem is not None:
            prestador_data['regTrib'] = {
                'opSimpNac': int(get_text(reg_trib_elem, 'opSimpNac', '1')),
                'regEspTrib': int(get_text(reg_trib_elem, 'regEspTrib', '0')),
                'regApTribSN': None
            }
            
            reg_ap_trib = get_text(reg_trib_elem, 'regApTribSN')
            if reg_ap_trib:
                prestador_data['regTrib']['regApTribSN'] = int(reg_ap_trib)
        else:
            # Regime tributário padrão se não encontrado
            prestador_data['regTrib'] = {
                'opSimpNac': 1,
                'regEspTrib': 0,
                'regApTribSN': None
            }
        
        # === 7. Extrair dados do tomador ===
        if not SILENT:
            print("👥 Extraindo dados do tomador...")
        
        toma_elem = find_element(inf_nfse, 'toma')
        if toma_elem is None:
            print("❌ Erro: Não foi possível encontrar elemento 'toma' no XML")
            return 3
        
        # Extrair dados do tomador
        tomador_data = {}
        
        # CNPJ ou CPF
        cnpj = get_text(toma_elem, 'CNPJ')
        cpf = get_text(toma_elem, 'CPF')
        if cnpj:
            tomador_data['CNPJ'] = cnpj
        elif cpf:
            tomador_data['CPF'] = cpf
        
        tomador_data['xNome'] = get_text(toma_elem, 'xNome')
        tomador_data['email'] = get_text(toma_elem, 'email') or None
        
        # Extrair endereço
        end_elem = find_element(toma_elem, 'end')
        if end_elem is not None:
            tomador_data['end'] = {
                'xLgr': get_text(end_elem, 'xLgr'),
                'nro': get_text(end_elem, 'nro'),
                'xBairro': get_text(end_elem, 'xBairro'),
                'cMun': get_text(end_elem, 'cMun'),
                'CEP': get_text(end_elem, 'CEP')
            }
            
            # Tentar buscar cMun e CEP dentro de endNac se não encontrados diretamente
            end_nac_elem = find_element(end_elem, 'endNac')
            if end_nac_elem is not None:
                if not tomador_data['end']['cMun']:
                    tomador_data['end']['cMun'] = get_text(end_nac_elem, 'cMun')
                if not tomador_data['end']['CEP']:
                    tomador_data['end']['CEP'] = get_text(end_nac_elem, 'CEP')
        
        # === 8. Extrair dados do serviço ===
        if not SILENT:
            print("📋 Extraindo dados do serviço...")
        
        serv_elem = find_element(inf_nfse, 'serv')
        if serv_elem is None:
            print("❌ Erro: Não foi possível encontrar elemento 'serv' no XML")
            return 3
        
        # Extrair dados do serviço
        servico_data = {}
        
        # Buscar cServ
        c_serv_elem = find_element(serv_elem, 'cServ')
        if c_serv_elem is not None:
            servico_data['cTribNac'] = get_text(c_serv_elem, 'cTribNac')
            servico_data['xDescServ'] = get_text(c_serv_elem, 'xDescServ')
            servico_data['cTribMun'] = get_text(c_serv_elem, 'cTribMun') or None
            servico_data['cNBS'] = get_text(c_serv_elem, 'cNBS') or None
        else:
            # Tentar buscar diretamente no serv
            servico_data['cTribNac'] = get_text(serv_elem, 'cTribNac')
            servico_data['xDescServ'] = get_text(serv_elem, 'xDescServ')
            servico_data['cTribMun'] = get_text(serv_elem, 'cTribMun') or None
            servico_data['cNBS'] = get_text(serv_elem, 'cNBS') or None
        
        # Buscar locPrest
        loc_prest_elem = find_element(serv_elem, 'locPrest')
        if loc_prest_elem is not None:
            servico_data['cLocPrestacao'] = get_text(loc_prest_elem, 'cLocPrestacao')
        else:
            servico_data['cLocPrestacao'] = get_text(serv_elem, 'cLocPrestacao')
        
        servico_data['cIntContrib'] = get_text(serv_elem, 'cIntContrib') or None
        
        # === 9. Salvar arquivos JSON ===
        timestamp = FileManager.gerar_timestamp()
        
        # Criar diretórios se não existirem
        for diretorio in ['prestadores', 'tomadores', 'servicos']:
            if not os.path.exists(diretorio):
                os.makedirs(diretorio, exist_ok=True)
        
        # Salvar prestador
        nome_arquivo_prestador = f"prestador_{timestamp}.json"
        caminho_prestador = os.path.join('prestadores', nome_arquivo_prestador)
        
        try:
            with open(caminho_prestador, 'w', encoding='utf-8') as f:
                json.dump(prestador_data, f, indent=2, ensure_ascii=False)
            if not SILENT:
                print(f"✓ Prestador salvo: {caminho_prestador}")
        except Exception as e:
            print(f"❌ Erro ao salvar prestador: {e}")
            return 4
        
        # Salvar tomador
        nome_arquivo_tomador = f"tomador_{timestamp}.json"
        caminho_tomador = os.path.join('tomadores', nome_arquivo_tomador)
        
        try:
            with open(caminho_tomador, 'w', encoding='utf-8') as f:
                json.dump(tomador_data, f, indent=2, ensure_ascii=False)
            if not SILENT:
                print(f"✓ Tomador salvo: {caminho_tomador}")
        except Exception as e:
            print(f"❌ Erro ao salvar tomador: {e}")
            return 4
        
        # Salvar serviço
        nome_arquivo_servico = f"servico_{timestamp}.json"
        caminho_servico = os.path.join('servicos', nome_arquivo_servico)
        
        try:
            with open(caminho_servico, 'w', encoding='utf-8') as f:
                json.dump(servico_data, f, indent=2, ensure_ascii=False)
            if not SILENT:
                print(f"✓ Serviço salvo: {caminho_servico}")
        except Exception as e:
            print(f"❌ Erro ao salvar serviço: {e}")
            return 4
        
        # === 10. Exibir mensagem de sucesso ===
        if not SILENT:
            print(f"\n✅ Importação concluída com sucesso!")
            print(f"   Arquivos criados:")
            print(f"   - {caminho_prestador}")
            print(f"   - {caminho_tomador}")
            print(f"   - {caminho_servico}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        return 1
