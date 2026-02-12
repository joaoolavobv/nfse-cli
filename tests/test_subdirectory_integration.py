"""
Testes de integração para suporte a subdiretórios.

Este módulo testa o fluxo completo de uso de arquivos em subdiretórios,
conforme Requisito 17: Suporte a Múltiplos Prestadores e Tomadores.
"""

import pytest
import os
import tempfile
from nfse_core.models import Prestador, Tomador, Servico, RegimeTributario, Endereco


class TestSubdirectoryIntegration:
    """Testes de integração para suporte a subdiretórios"""
    
    def test_workflow_completo_com_subdiretorios(self):
        """
        Testa fluxo completo de criação e carregamento de arquivos em subdiretórios.
        
        Simula um cenário real onde um usuário organiza seus arquivos em:
        - prestadores/empresa_a/prestador.json
        - tomadores/clientes/cliente_especial.json
        - servicos/consultoria/servico.json
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # === Criar estrutura de diretórios ===
            prestador_path = os.path.join(tmpdir, "prestadores", "empresa_a", "prestador.json")
            tomador_path = os.path.join(tmpdir, "tomadores", "clientes", "cliente_especial.json")
            servico_path = os.path.join(tmpdir, "servicos", "consultoria", "servico.json")
            
            # === Criar e salvar prestador ===
            regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
            prestador = Prestador(
                CNPJ="12345678000190",
                xNome="EMPRESA A LTDA",
                cMun="3550308",
                IM="12345678",
                email="contato@empresaa.com",
                regTrib=regime
            )
            prestador.salvar(prestador_path)
            
            # === Criar e salvar tomador ===
            endereco = Endereco(
                xLgr="Rua Especial",
                nro="999",
                xBairro="Centro",
                cMun="3550308",
                CEP="01234567"
            )
            tomador = Tomador(
                CNPJ="98765432000100",
                xNome="CLIENTE ESPECIAL LTDA",
                email="financeiro@clienteespecial.com",
                end=endereco
            )
            tomador.salvar(tomador_path)
            
            # === Criar e salvar serviço ===
            servico = Servico(
                xDescServ="SERVICOS DE CONSULTORIA ESPECIALIZADA",
                cTribNac="010101",
                cLocPrestacao="3550308",
                cTribMun="001"
            )
            servico.salvar(servico_path)
            
            # === Verificar que os diretórios foram criados ===
            assert os.path.exists(os.path.dirname(prestador_path))
            assert os.path.exists(os.path.dirname(tomador_path))
            assert os.path.exists(os.path.dirname(servico_path))
            
            # === Verificar que os arquivos foram criados ===
            assert os.path.exists(prestador_path)
            assert os.path.exists(tomador_path)
            assert os.path.exists(servico_path)
            
            # === Carregar arquivos usando caminhos relativos com subdiretórios ===
            # Simula o que acontece quando o usuário usa:
            # --prestador prestadores/empresa_a/prestador.json
            # --tomador tomadores/clientes/cliente_especial.json
            # --servico servicos/consultoria/servico.json
            
            prestador_carregado = Prestador.carregar(prestador_path)
            tomador_carregado = Tomador.carregar(tomador_path)
            servico_carregado = Servico.carregar(servico_path)
            
            # === Validar dados carregados ===
            assert prestador_carregado.CNPJ == "12345678000190"
            assert prestador_carregado.xNome == "EMPRESA A LTDA"
            assert prestador_carregado.regTrib.opSimpNac == 1
            
            assert tomador_carregado.CNPJ == "98765432000100"
            assert tomador_carregado.xNome == "CLIENTE ESPECIAL LTDA"
            assert tomador_carregado.end.xLgr == "Rua Especial"
            
            assert servico_carregado.xDescServ == "SERVICOS DE CONSULTORIA ESPECIALIZADA"
            assert servico_carregado.cTribNac == "010101"
            
            # === Validar que os dados são válidos ===
            assert len(prestador_carregado.validar()) == 0
            assert len(tomador_carregado.validar()) == 0
            assert len(servico_carregado.validar()) == 0
    
    def test_erro_claro_para_arquivo_inexistente_em_subdiretorio(self):
        """
        Testa que mensagens de erro são claras quando arquivo não existe em subdiretório.
        
        Requisito 17.4: Validar existência do arquivo antes de tentar ler.
        """
        # Tentar carregar arquivo que não existe em subdiretório profundo
        caminho_inexistente = "prestadores/empresa_x/filial_y/prestador.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            Prestador.carregar(caminho_inexistente)
        
        # Verificar que a mensagem de erro contém o caminho completo
        erro_msg = str(exc_info.value)
        assert caminho_inexistente in erro_msg
        assert "Arquivo não encontrado" in erro_msg
    
    def test_multiplos_prestadores_organizados(self):
        """
        Testa cenário de múltiplos prestadores organizados em subdiretórios.
        
        Simula estrutura:
        prestadores/
          ├── empresa_a/
          │   └── prestador.json
          ├── empresa_b/
          │   └── prestador.json
          └── empresa_c/
              └── prestador.json
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            empresas = ["empresa_a", "empresa_b", "empresa_c"]
            prestadores_criados = []
            
            # Criar múltiplos prestadores em subdiretórios
            for i, empresa in enumerate(empresas):
                caminho = os.path.join(tmpdir, "prestadores", empresa, "prestador.json")
                
                regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
                prestador = Prestador(
                    CNPJ=f"1234567800019{i}",
                    xNome=f"{empresa.upper()} LTDA",
                    cMun="3550308",
                    regTrib=regime
                )
                prestador.salvar(caminho)
                prestadores_criados.append((caminho, prestador))
            
            # Carregar e validar cada prestador
            for caminho, prestador_original in prestadores_criados:
                prestador_carregado = Prestador.carregar(caminho)
                assert prestador_carregado.CNPJ == prestador_original.CNPJ
                assert prestador_carregado.xNome == prestador_original.xNome
                assert len(prestador_carregado.validar()) == 0
