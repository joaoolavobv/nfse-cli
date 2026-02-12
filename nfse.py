#!/usr/bin/env python3
"""
Entry point para nfse-cli.

Este arquivo serve como ponto de entrada principal para a aplicação,
delegando a execução para o módulo CLI.
"""

import warnings
import sys

# Suprimir warnings de deprecação do signxml relacionados a algoritmos SECT
# que serão removidos em versões futuras do cryptography.
# Isso não afeta a funcionalidade pois usamos apenas RSA-SHA1 para assinatura XML.
# TODO: Remover quando signxml for atualizado para não usar esses algoritmos.
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except ImportError:
    pass

from nfse_core.cli import main

if __name__ == '__main__':
    sys.exit(main())
