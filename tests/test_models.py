"""
Testes para o módulo de modelos de dados.
"""

import pytest
import json
import os
import tempfile
from nfse_core.models import Endereco, RegimeTributario, Prestador, Tomador, Servico


class TestEndereco:
    """Testes para a classe Endereco"""
    
    def test_endereco_valido(self):
        """Testa criação de endereço válido"""
        endereco = Endereco(
            xLgr="Avenida Paulista",
            nro="1000",
            xBairro="Bela Vista",
            cMun="3550308",
            CEP="01310100"
        )
        erros = endereco.validar()
        assert len(erros) == 0
    
    def test_endereco_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        endereco = Endereco()
        erros = endereco.validar()
        assert len(erros) == 5  # Todos os campos são obrigatórios
        assert any("xLgr" in erro for erro in erros)
        assert any("nro" in erro for erro in erros)
        assert any("xBairro" in erro for erro in erros)
        assert any("cMun" in erro for erro in erros)
        assert any("CEP" in erro for erro in erros)
    
    def test_endereco_cmun_invalido(self):
        """Testa validação de código de município inválido"""
        endereco = Endereco(
            xLgr="Rua Teste",
            nro="123",
            xBairro="Centro",
            cMun="123",  # Deve ter 7 dígitos
            CEP="12345678"
        )
        erros = endereco.validar()
        assert any("cMun" in erro and "7 dígitos" in erro for erro in erros)
    
    def test_endereco_cep_invalido(self):
        """Testa validação de CEP inválido"""
        endereco = Endereco(
            xLgr="Rua Teste",
            nro="123",
            xBairro="Centro",
            cMun="3550308",
            CEP="123"  # Deve ter 8 dígitos
        )
        erros = endereco.validar()
        assert any("CEP" in erro and "8 dígitos" in erro for erro in erros)


class TestRegimeTributario:
    """Testes para a classe RegimeTributario"""
    
    def test_regime_valido_nao_optante(self):
        """Testa regime tributário válido para não optante do Simples"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
        erros = regime.validar()
        assert len(erros) == 0
    
    def test_regime_valido_mei(self):
        """Testa regime tributário válido para MEI"""
        regime = RegimeTributario(opSimpNac=2, regEspTrib=0)
        erros = regime.validar()
        assert len(erros) == 0
    
    def test_regime_valido_me_epp_com_reg_ap(self):
        """Testa regime tributário válido para ME/EPP com regApTribSN"""
        regime = RegimeTributario(opSimpNac=3, regEspTrib=0, regApTribSN=1)
        erros = regime.validar()
        assert len(erros) == 0
    
    def test_regime_op_simp_nac_invalido(self):
        """Testa validação de opSimpNac inválido"""
        regime = RegimeTributario(opSimpNac=5, regEspTrib=0)
        erros = regime.validar()
        assert any("opSimpNac" in erro for erro in erros)
    
    def test_regime_reg_esp_trib_invalido(self):
        """Testa validação de regEspTrib inválido"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=7)
        erros = regime.validar()
        assert any("regEspTrib" in erro for erro in erros)
    
    def test_regime_reg_ap_trib_sn_sem_op_simp_nac_3(self):
        """Testa que regApTribSN só é permitido quando opSimpNac=3"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=0, regApTribSN=1)
        erros = regime.validar()
        assert any("regApTribSN" in erro and "opSimpNac" in erro for erro in erros)
    
    def test_regime_reg_ap_trib_sn_invalido(self):
        """Testa validação de regApTribSN inválido"""
        regime = RegimeTributario(opSimpNac=3, regEspTrib=0, regApTribSN=5)
        erros = regime.validar()
        assert any("regApTribSN" in erro for erro in erros)


class TestPrestador:
    """Testes para a classe Prestador"""
    
    def test_prestador_valido_com_cnpj(self):
        """Testa criação de prestador válido com CNPJ"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
        prestador = Prestador(
            CNPJ="12345678000190",
            xNome="EMPRESA TESTE LTDA",
            cMun="3550308",
            regTrib=regime
        )
        erros = prestador.validar()
        assert len(erros) == 0
    
    def test_prestador_valido_com_cpf(self):
        """Testa criação de prestador válido com CPF"""
        regime = RegimeTributario(opSimpNac=2, regEspTrib=0)
        prestador = Prestador(
            CPF="12345678901",
            xNome="JOAO DA SILVA",
            cMun="3550308",
            regTrib=regime
        )
        erros = prestador.validar()
        assert len(erros) == 0
    
    def test_prestador_sem_documento(self):
        """Testa validação de prestador sem CNPJ nem CPF"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
        prestador = Prestador(
            xNome="EMPRESA TESTE",
            cMun="3550308",
            regTrib=regime
        )
        erros = prestador.validar()
        assert any("CNPJ" in erro or "CPF" in erro for erro in erros)
    
    def test_prestador_com_cnpj_e_cpf(self):
        """Testa validação de prestador com CNPJ e CPF simultaneamente"""
        regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
        prestador = Prestador(
            CNPJ="12345678000190",
            CPF="12345678901",
            xNome="EMPRESA TESTE",
            cMun="3550308",
            regTrib=regime
        )
        erros = prestador.validar()
        assert any("Apenas um" in erro for erro in erros)
    
    def test_prestador_sem_reg_trib(self):
        """Testa validação de prestador sem regime tributário"""
        prestador = Prestador(
            CNPJ="12345678000190",
            xNome="EMPRESA TESTE",
            cMun="3550308"
        )
        erros = prestador.validar()
        assert any("regTrib" in erro for erro in erros)
    
    def test_prestador_obter_documento_cnpj(self):
        """Testa método obter_documento com CNPJ"""
        prestador = Prestador(CNPJ="12345678000190")
        assert prestador.obter_documento() == "12345678000190"
    
    def test_prestador_obter_documento_cpf(self):
        """Testa método obter_documento com CPF"""
        prestador = Prestador(CPF="12345678901")
        assert prestador.obter_documento() == "12345678901"
    
    def test_prestador_carregar_salvar(self):
        """Testa carregamento e salvamento de prestador"""
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, "prestador_teste.json")
            
            # Criar e salvar prestador
            regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
            prestador_original = Prestador(
                CNPJ="12345678000190",
                xNome="EMPRESA TESTE LTDA",
                cMun="3550308",
                IM="12345678",
                email="teste@empresa.com",
                regTrib=regime
            )
            prestador_original.salvar(caminho)
            
            # Carregar prestador
            prestador_carregado = Prestador.carregar(caminho)
            
            # Verificar dados
            assert prestador_carregado.CNPJ == prestador_original.CNPJ
            assert prestador_carregado.xNome == prestador_original.xNome
            assert prestador_carregado.cMun == prestador_original.cMun
            assert prestador_carregado.regTrib.opSimpNac == regime.opSimpNac
    
    def test_prestador_carregar_com_subdiretorio(self):
        """Testa carregamento de prestador em subdiretório"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Criar caminho com subdiretório
            subdir = os.path.join(tmpdir, "empresa_a", "filial_sp")
            caminho = os.path.join(subdir, "prestador.json")
            
            # Criar e salvar prestador
            regime = RegimeTributario(opSimpNac=1, regEspTrib=0)
            prestador_original = Prestador(
                CNPJ="12345678000190",
                xNome="EMPRESA TESTE LTDA",
                cMun="3550308",
                regTrib=regime
            )
            prestador_original.salvar(caminho)
            
            # Verificar que o diretório foi criado
            assert os.path.exists(subdir)
            assert os.path.exists(caminho)
            
            # Carregar prestador
            prestador_carregado = Prestador.carregar(caminho)
            
            # Verificar dados
            assert prestador_carregado.CNPJ == prestador_original.CNPJ
            assert prestador_carregado.xNome == prestador_original.xNome
    
    def test_prestador_carregar_arquivo_inexistente(self):
        """Testa erro ao carregar prestador de arquivo inexistente"""
        caminho = "prestadores/nao_existe/prestador.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            Prestador.carregar(caminho)
        
        # Verificar que a mensagem de erro contém o caminho
        assert caminho in str(exc_info.value)
    
    def test_prestador_carregar_subdiretorio_inexistente(self):
        """Testa erro ao carregar prestador de subdiretório inexistente"""
        caminho = "prestadores/empresa_x/filial_y/prestador.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            Prestador.carregar(caminho)
        
        # Verificar que a mensagem de erro contém o caminho completo
        assert caminho in str(exc_info.value)


class TestTomador:
    """Testes para a classe Tomador"""
    
    def test_tomador_valido_com_cnpj(self):
        """Testa criação de tomador válido com CNPJ"""
        tomador = Tomador(
            CNPJ="98765432000100",
            xNome="CLIENTE TESTE LTDA"
        )
        erros = tomador.validar()
        assert len(erros) == 0
    
    def test_tomador_valido_com_endereco(self):
        """Testa criação de tomador válido com endereço"""
        endereco = Endereco(
            xLgr="Rua Teste",
            nro="100",
            xBairro="Centro",
            cMun="3550308",
            CEP="01234567"
        )
        tomador = Tomador(
            CNPJ="98765432000100",
            xNome="CLIENTE TESTE LTDA",
            end=endereco
        )
        erros = tomador.validar()
        assert len(erros) == 0
    
    def test_tomador_sem_documento(self):
        """Testa validação de tomador sem CNPJ nem CPF"""
        tomador = Tomador(xNome="CLIENTE TESTE")
        erros = tomador.validar()
        assert any("CNPJ" in erro or "CPF" in erro for erro in erros)
    
    def test_tomador_obter_documento(self):
        """Testa método obter_documento"""
        tomador = Tomador(CNPJ="98765432000100")
        assert tomador.obter_documento() == "98765432000100"
    
    def test_tomador_carregar_salvar(self):
        """Testa carregamento e salvamento de tomador"""
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, "tomador_teste.json")
            
            # Criar e salvar tomador
            endereco = Endereco(
                xLgr="Rua Teste",
                nro="100",
                xBairro="Centro",
                cMun="3550308",
                CEP="01234567"
            )
            tomador_original = Tomador(
                CNPJ="98765432000100",
                xNome="CLIENTE TESTE LTDA",
                email="cliente@teste.com",
                end=endereco
            )
            tomador_original.salvar(caminho)
            
            # Carregar tomador
            tomador_carregado = Tomador.carregar(caminho)
            
            # Verificar dados
            assert tomador_carregado.CNPJ == tomador_original.CNPJ
            assert tomador_carregado.xNome == tomador_original.xNome
            assert tomador_carregado.end.xLgr == endereco.xLgr
    
    def test_tomador_carregar_com_subdiretorio(self):
        """Testa carregamento de tomador em subdiretório"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Criar caminho com subdiretório
            subdir = os.path.join(tmpdir, "clientes", "especiais")
            caminho = os.path.join(subdir, "tomador.json")
            
            # Criar e salvar tomador
            tomador_original = Tomador(
                CNPJ="98765432000100",
                xNome="CLIENTE ESPECIAL LTDA"
            )
            tomador_original.salvar(caminho)
            
            # Verificar que o diretório foi criado
            assert os.path.exists(subdir)
            assert os.path.exists(caminho)
            
            # Carregar tomador
            tomador_carregado = Tomador.carregar(caminho)
            
            # Verificar dados
            assert tomador_carregado.CNPJ == tomador_original.CNPJ
            assert tomador_carregado.xNome == tomador_original.xNome
    
    def test_tomador_carregar_arquivo_inexistente(self):
        """Testa erro ao carregar tomador de arquivo inexistente"""
        caminho = "tomadores/nao_existe/tomador.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            Tomador.carregar(caminho)
        
        # Verificar que a mensagem de erro contém o caminho
        assert caminho in str(exc_info.value)


class TestServico:
    """Testes para a classe Servico"""
    
    def test_servico_valido(self):
        """Testa criação de serviço válido"""
        servico = Servico(
            xDescServ="SERVICOS DE CONSULTORIA EM TECNOLOGIA",
            cTribNac="010101",
            cLocPrestacao="3550308"
        )
        erros = servico.validar()
        assert len(erros) == 0
    
    def test_servico_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        servico = Servico()
        erros = servico.validar()
        assert len(erros) == 3  # xDescServ, cTribNac, cLocPrestacao
        assert any("xDescServ" in erro for erro in erros)
        assert any("cTribNac" in erro for erro in erros)
        assert any("cLocPrestacao" in erro for erro in erros)
    
    def test_servico_ctrib_nac_invalido(self):
        """Testa validação de código de tributação nacional inválido"""
        servico = Servico(
            xDescServ="SERVICOS DE TESTE",
            cTribNac="0101",  # Deve ter 6 dígitos
            cLocPrestacao="3550308"
        )
        erros = servico.validar()
        assert any("cTribNac" in erro and "6 dígitos" in erro for erro in erros)
    
    def test_servico_cloc_prestacao_invalido(self):
        """Testa validação de código de local de prestação inválido"""
        servico = Servico(
            xDescServ="SERVICOS DE TESTE",
            cTribNac="010101",
            cLocPrestacao="355"  # Deve ter 7 dígitos
        )
        erros = servico.validar()
        assert any("cLocPrestacao" in erro and "7 dígitos" in erro for erro in erros)
    
    def test_servico_ctrib_mun_invalido(self):
        """Testa validação de código de tributação municipal inválido"""
        servico = Servico(
            xDescServ="SERVICOS DE TESTE",
            cTribNac="010101",
            cLocPrestacao="3550308",
            cTribMun="12"  # Deve ter 3 dígitos
        )
        erros = servico.validar()
        assert any("cTribMun" in erro and "3 dígitos" in erro for erro in erros)
    
    def test_servico_nao_aceita_vserv(self):
        """Testa que serviço não aceita campo vServ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, "servico_teste.json")
            
            # Criar JSON com campo proibido
            dados = {
                "xDescServ": "SERVICOS DE TESTE",
                "cTribNac": "010101",
                "cLocPrestacao": "3550308",
                "vServ": 1500.00  # Campo proibido
            }
            
            with open(caminho, 'w') as f:
                json.dump(dados, f)
            
            # Tentar carregar deve gerar erro
            with pytest.raises(ValueError) as exc_info:
                Servico.carregar(caminho)
            
            assert "vServ" in str(exc_info.value)
    
    def test_servico_nao_aceita_dhemi(self):
        """Testa que serviço não aceita campo dhEmi"""
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, "servico_teste.json")
            
            # Criar JSON com campo proibido
            dados = {
                "xDescServ": "SERVICOS DE TESTE",
                "cTribNac": "010101",
                "cLocPrestacao": "3550308",
                "dhEmi": "2024-01-15T14:30:00-03:00"  # Campo proibido
            }
            
            with open(caminho, 'w') as f:
                json.dump(dados, f)
            
            # Tentar carregar deve gerar erro
            with pytest.raises(ValueError) as exc_info:
                Servico.carregar(caminho)
            
            assert "dhEmi" in str(exc_info.value)
    
    def test_servico_carregar_salvar(self):
        """Testa carregamento e salvamento de serviço"""
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, "servico_teste.json")
            
            # Criar e salvar serviço
            servico_original = Servico(
                xDescServ="SERVICOS DE CONSULTORIA EM TECNOLOGIA",
                cTribNac="010101",
                cLocPrestacao="3550308",
                cTribMun="001",
                cNBS="123456"
            )
            servico_original.salvar(caminho)
            
            # Carregar serviço
            servico_carregado = Servico.carregar(caminho)
            
            # Verificar dados
            assert servico_carregado.xDescServ == servico_original.xDescServ
            assert servico_carregado.cTribNac == servico_original.cTribNac
            assert servico_carregado.cLocPrestacao == servico_original.cLocPrestacao
    
    def test_servico_carregar_com_subdiretorio(self):
        """Testa carregamento de serviço em subdiretório"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Criar caminho com subdiretório
            subdir = os.path.join(tmpdir, "servicos", "consultoria")
            caminho = os.path.join(subdir, "servico.json")
            
            # Criar e salvar serviço
            servico_original = Servico(
                xDescServ="SERVICOS DE CONSULTORIA",
                cTribNac="010101",
                cLocPrestacao="3550308"
            )
            servico_original.salvar(caminho)
            
            # Verificar que o diretório foi criado
            assert os.path.exists(subdir)
            assert os.path.exists(caminho)
            
            # Carregar serviço
            servico_carregado = Servico.carregar(caminho)
            
            # Verificar dados
            assert servico_carregado.xDescServ == servico_original.xDescServ
            assert servico_carregado.cTribNac == servico_original.cTribNac
    
    def test_servico_carregar_arquivo_inexistente(self):
        """Testa erro ao carregar serviço de arquivo inexistente"""
        caminho = "servicos/nao_existe/servico.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            Servico.carregar(caminho)
        
        # Verificar que a mensagem de erro contém o caminho
        assert caminho in str(exc_info.value)
