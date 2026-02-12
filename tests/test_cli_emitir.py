"""
Testes para o comando emitir do CLI.

Testa validações e fluxo básico do comando emitir.
"""

import pytest
import sys
import os
from argparse import Namespace

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nfse_core.cli import executar_emitir, VERBOSE, SILENT


class TestExecutarEmitir:
    """Testes para a função executar_emitir"""
    
    def test_emitir_sem_valor_retorna_erro(self, monkeypatch):
        """Testa que emitir sem --valor retorna código de erro 1"""
        # Criar args sem valor
        args = Namespace(
            valor=None,
            data="2024-01-15",
            ambiente=None,
            dry_run=None,
            prestador=None,
            tomador=None,
            servico=None
        )
        
        # Executar comando
        codigo_saida = executar_emitir(args)
        
        # Verificar que retornou erro
        assert codigo_saida == 1
    
    def test_emitir_sem_data_retorna_erro(self, monkeypatch):
        """Testa que emitir sem --data retorna código de erro 1"""
        # Criar args sem data
        args = Namespace(
            valor=1500.00,
            data=None,
            ambiente=None,
            dry_run=None,
            prestador=None,
            tomador=None,
            servico=None
        )
        
        # Executar comando
        codigo_saida = executar_emitir(args)
        
        # Verificar que retornou erro
        assert codigo_saida == 1
    
    def test_emitir_com_valor_negativo_retorna_erro(self, monkeypatch):
        """Testa que emitir com valor negativo retorna código de erro 1"""
        # Criar args com valor negativo
        args = Namespace(
            valor=-100.00,
            data="2024-01-15",
            ambiente=None,
            dry_run=None,
            prestador=None,
            tomador=None,
            servico=None
        )
        
        # Executar comando
        codigo_saida = executar_emitir(args)
        
        # Verificar que retornou erro
        assert codigo_saida == 1
    
    def test_emitir_com_data_invalida_retorna_erro(self, monkeypatch):
        """Testa que emitir com data inválida retorna código de erro 1"""
        # Criar args com data inválida (formato incorreto)
        args = Namespace(
            valor=1500.00,
            data="2024-15-01",  # Formato inválido (mês 15 não existe)
            ambiente=None,
            dry_run=None,
            prestador=None,
            tomador=None,
            servico=None
        )
        
        # Executar comando
        codigo_saida = executar_emitir(args)
        
        # Verificar que retornou erro
        assert codigo_saida == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
