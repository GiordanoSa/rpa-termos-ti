# ==============================================================================
# 🤖 AUTOMAÇÃO DE TERMOS DE TI E ASSINATURA ELETRÔNICA (RPA)
# ==============================================================================
# Desenvolvido por : [SEU NOME]
# Ano              : 2026
# Descrição        : Script genérico de RPA em Python (Selenium) criado para 
#                    orquestrar a extração de ativos em plataforma ITSM genérica, 
#                    geração dinâmica de documentos em nuvem e disparo de 
#                    assinaturas digitais.
#                    *CÓDIGO SANITIZADO - LIVRE DE DADOS SENSÍVEIS*
# ==============================================================================

import os
import re
import time
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==============================================================================
# ⚙️ VARIÁVEIS GLOBAIS DE CONFIGURAÇÃO (TEMPLATE)
# ==============================================================================
DOMINIO_EMAIL = "@empresa.com.br"
NOME_EQUIPE = "Equipe de TI"

URL_SISTEMA = "https://sistema-itsm-generico.com.br/"

URL_TPL_1 = "URL_DO_TEMPLATE_1_AQUI"
URL_TPL_2 = "URL_DO_TEMPLATE_2_AQUI"
URL_TPL_3 = "URL_DO_TEMPLATE_3_AQUI"

PASTA_NUVEM_A = "ID_DA_PASTA_A_AQUI"
PASTA_NUVEM_B = "ID_DA_PASTA_B_AQUI"

EMAIL_TESTEMUNHA_1 = f"tecnico1{DOMINIO_EMAIL}"
EMAIL_TESTEMUNHA_2 = f"tecnico2{DOMINIO_EMAIL}"
EMAIL_TESTEMUNHA_3 = f"terceiro_projeto@parceiro.com"

VALOR_PADRAO = "R$ 7.000,00"
# ==============================================================================

def limpar_nome_arquivo(texto: str) -> str:
    texto_limpo = re.sub(r'[\\/*?:"<>|]', "", str(texto))
    return texto_limpo.replace(" ", "_").strip()

def prever_email_colaborador(nome_completo: str) -> str:
    partes = nome_completo.strip().lower().split()
    if len(partes) >= 2:
        primeiro = re.sub(r"[^a-z]", "", partes[0])
        ultimo = re.sub(r"[^a-z]", "", partes[-1])
        return f"{primeiro}.{ultimo}{DOMINIO_EMAIL}"
    elif len(partes) == 1:
        primeiro = re.sub(r"[^a-z]", "", partes[0])
        return f"{primeiro}{DOMINIO_EMAIL}"
    return ""

def inferir_tipo_equipamento(tipo_raw: str, modelo: str, hostname: str) -> str:
    if tipo_raw and tipo_raw.strip():
        return tipo_raw.strip().title()
    
    texto = f"{modelo} {hostname}".lower()
    if any(t in texto for t in ["ntb", "notebook", "laptop"]):
        return "Notebook"
    elif any(t in texto for t in ["mon", "monitor", "display"]):
        return "Monitor"
    elif any(t in texto for t in ["cel", "celular", "smartphone"]):
        return "Celular"
    elif any(t in texto for t in ["desk", "desktop"]):
        return "Desktop"
    return "Notebook"

def obter_valor_por_modelo(modelo: str) -> str:
    return input(f"\n⚠️ Digite o valor do modelo '{modelo}' (ex: R$ 5.000,00): ").strip()

def clicar_seguro(driver, elemento):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", elemento)
        time.sleep(0.3)
        elemento.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elemento)

def preencher_campo_seguro(driver, elemento, texto):
    texto_str = str(texto).strip()
    texto_tratado = texto_str.lower() if "@" in texto_str else texto_str
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        time.sleep(0.1)
        driver.execute_script("arguments[0].focus();", elemento)
        elemento.click()
        time.sleep(0.1)
        try: elemento.clear()
        except: pass
        driver.execute_script("arguments[0].value = '';", elemento)
        elemento.send_keys(Keys.CONTROL + "a")
        elemento.send_keys(Keys.BACKSPACE)
        time.sleep(0.1)
        elemento.send_keys(texto_tratado)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", elemento)
    except Exception:
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, elemento, texto_tratado)

def extrair_ativos_itsm(driver, wait, chave, coluna=None):
    driver.get(f"{URL_SISTEMA}Itens")
    try:
        wait.until(EC.presence_of_element_located((By.ID, "grid")))
        time.sleep(2)
    except:
        return []

    campo_coluna = coluna if coluna else ("HostName" if "NTB" in chave.upper() else "UsuarioLogin")
    print(f"Filtro aplicado: [{campo_coluna} = '{chave}']...")
    
    script_kendo_filter = f"""
    var grid = $("#grid").data("kendoGrid") || $(".k-grid").data("kendoGrid");
    if(grid) grid.dataSource.filter({{ field: "{campo_coluna}", operator: "contains", value: "{chave}" }});
    """
    driver.execute_script(script_kendo_filter)

    lista_ativos = []
    print("⏳ Extraindo dados do sistema...")
    
    for _ in range(10):
        time.sleep(1.5)
        script_extrair_js = f"""
        var busca = "{chave}".toUpperCase();
        var lista = [];
        try {{
            var grid = $("#grid").data("kendoGrid") || $(".k-grid").data("kendoGrid");
            if (grid && grid.dataSource) {{
                var view = grid.dataSource.view();
                for (var i = 0; i < view.length; i++) {{
                    var item = view[i];
                    if (JSON.stringify(item).toUpperCase().indexOf(busca) !== -1) {{
                        lista.push({{
                            modelo: item.Modelo || "", serial: item.Serial || "",
                            patrimonio: item.Patrimonio || "", hostname: item.HostName || "",
                            nome_colab: item.Usuario || "", matricula: item.UsuarioLogin || "",
                            area: item.Setor || "", tipo_raw: item.Tipo || ""
                        }});
                    }}
                }}
            }}
        }} catch(e) {{}}
        return lista;
        """
        lista_ativos = driver.execute_script(script_extrair_js)
        if lista_ativos: break

    return lista_ativos

def mover_documento_nuvem(driver, wait, id_pasta, nome_pasta):
    try:
        print(f"📂 Alocando na pasta {nome_pasta}...")
        time.sleep(1.5)
        xpath_btn_mover = "//div[@id='docs-folder-shortcut'] | //div[contains(@aria-label, 'Mover')]"
        btn_mover = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_btn_mover)))
        clicar_seguro(driver, btn_mover)

        iframe_xpath = "//iframe[contains(@class, 'picker')]"
        wait.until(EC.presence_of_element_located((By.XPATH, iframe_xpath)))
        time.sleep(1)

        iframes_picker = driver.find_elements(By.XPATH, iframe_xpath)
        if iframes_picker:
            driver.switch_to.frame(iframes_picker[-1])
            xpath_input = "//input[contains(@aria-label, 'Pesquisar') or @type='text']"
            wait.until(EC.presence_of_element_located((By.XPATH, xpath_input)))
            inputs_pasta = driver.find_elements(By.XPATH, xpath_input)
            
            inputs_visiveis = [i for i in inputs_pasta if i.is_displayed()]
            if inputs_visiveis:
                busca_box = inputs_visiveis[0]
                clicar_seguro(driver, busca_box)
                time.sleep(0.5)
                busca_box.send_keys(Keys.CONTROL + "a")
                busca_box.send_keys(Keys.BACKSPACE)
                busca_box.send_keys(id_pasta)
                time.sleep(0.5)
                busca_box.send_keys(Keys.ENTER)
                time.sleep(3) 
                
                busca_box.send_keys(Keys.TAB)
                time.sleep(0.5)
                ActionChains(driver).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()
                time.sleep(1.5)

                xpath_btn_confirmar = "//button[contains(., 'Mover para cá')]"
                botoes_confirmar = driver.find_elements(By.XPATH, xpath_btn_confirmar)
                for b in botoes_confirmar:
                    if b.is_displayed():
                        clicar_seguro(driver, b)
                        break
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()
    finally:
        driver.switch_to.default_content()
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)

def executar_fluxo_docs(driver, wait, template_url, nome_documento, dados_dinamicos, 
                        tipo_empresa, email_recebedor, email_testemunha_1, email_testemunha_2, tipo_doc):
    url_fazer_copia = template_url.split('/edit')[0] + '/copy'
    driver.get(url_fazer_copia)
    time.sleep(3)

    if "accounts.google.com" in driver.current_url:
        input("📌 Faça o login e dê ENTER aqui...")
        if "copy" not in driver.current_url: driver.get(url_fazer_copia)

    try:
        xpath_btn_copia = "//div[@role='button' and contains(., 'cópia')] | //form//button"
        btn_copia = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_btn_copia)))
        clicar_seguro(driver, btn_copia)
        
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kix-appview-editor")))
        time.sleep(4) 

        input_titulo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "docs-title-input")))
        clicar_seguro(driver, input_titulo)
        preencher_campo_seguro(driver, input_titulo, nome_documento)
        input_titulo.send_keys(Keys.ENTER)
        time.sleep(1)

        if tipo_empresa == "1":
            if tipo_doc in ["Onboarding", "Entrega"]:
                mover_documento_nuvem(driver, wait, PASTA_NUVEM_A, "Pasta A")
        elif tipo_empresa == "2":
            mover_documento_nuvem(driver, wait, PASTA_NUVEM_B, "Pasta B")

        editor_canvas = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kix-appview-editor")))
        clicar_seguro(driver, editor_canvas)
        time.sleep(1)

        acoes = ActionChains(driver)
        acoes.key_down(Keys.CONTROL).send_keys('h').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        xpath_localizar = "//input[@aria-label='Localizar' or contains(@class, 'findinput')]"
        xpath_substituir = "//input[@aria-label='Substituir por' or contains(@class, 'replaceinput')]"
        xpath_btn_tudo = "//button[@name='replaceAll']"

        try:
            input_localizar = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_localizar)))
        except:
            acoes.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            clicar_seguro(driver, editor_canvas)
            acoes.key_down(Keys.CONTROL).send_keys('h').key_up(Keys.CONTROL).perform()
            input_localizar = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_localizar)))

        input_substituir = driver.find_element(By.XPATH, xpath_substituir)
        btn_substituir_tudo = driver.find_element(By.XPATH, xpath_btn_tudo)

        for tag, valor in dados_dinamicos.items():
            preencher_campo_seguro(driver, input_localizar, tag)
            time.sleep(0.2)
            preencher_campo_seguro(driver, input_substituir, valor)
            time.sleep(0.2)
            clicar_seguro(driver, btn_substituir_tudo)
            time.sleep(0.4)

        acoes.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

    except Exception:
        traceback.print_exc()

    mensagem_assinatura = f"Olá.\nSegue documento para assinatura.\nAtenciosamente, {NOME_EQUIPE}"

    try:
        time.sleep(2)
        botoes_painel = driver.find_elements(By.XPATH, "//button[contains(., 'Pedir assinatura')]")
        btn_painel_visivel = [b for b in botoes_painel if b.is_displayed()]

        if btn_painel_visivel:
            clicar_seguro(driver, btn_painel_visivel[0])
            time.sleep(2)
        else:
            menu_ferramentas = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='docs-tools-menu']")))
            clicar_seguro(driver, menu_ferramentas)
            time.sleep(0.8)
            item_esign = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(., 'eSignature') or contains(., 'Assinatura')]")))
            clicar_seguro(driver, item_esign)
            time.sleep(1.5)
            for b in driver.find_elements(By.XPATH, "//button[contains(., 'Pedir assinatura')]"):
                if b.is_displayed():
                    clicar_seguro(driver, b)
                    break

        time.sleep(2.5)
        driver.switch_to.default_content()
        inputs_dialog = driver.find_elements(By.XPATH, "//div[contains(@role, 'dialog')]//input")
        inputs_visiveis = [i for i in inputs_dialog if i.is_displayed()]

        campos_email = inputs_visiveis[1:4] if len(inputs_visiveis) >= 4 else inputs_visiveis
        lista_emails = [email_recebedor, email_testemunha_1, email_testemunha_2]

        for idx, em in enumerate(lista_emails):
            if idx < len(campos_email):
                preencher_campo_seguro(driver, campos_email[idx], em)
                time.sleep(0.4)

        textareas = driver.find_elements(By.XPATH, "//div[contains(@role, 'dialog')]//textarea")
        if textareas: preencher_campo_seguro(driver, textareas[0], mensagem_assinatura)

        time.sleep(2) 
        xpath_btn_disparar = "//div[contains(@role, 'dialog')]//button[contains(., 'Pedir')]"
        botoes_disparo = driver.find_elements(By.XPATH, xpath_btn_disparar)
        
        for btn in botoes_disparo:
            if btn.is_displayed():
                wait.until(lambda d: btn.is_enabled())
                clicar_seguro(driver, btn)
                break

        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

# =========================================================
# PROGRAMA PRINCIPAL
# =========================================================
print("=== 🤖 SISTEMA DE RPA - DOCUMENTAÇÃO ===")

tipo_empresa = input("Selecione a Organização: [1] INTERNA | [2] EXTERNA: ").strip()
empresa_rotulo = "INT" if tipo_empresa == "1" else "EXT"

tipo_termo = input("Processo: [1] ONBOARDING | [2] TROCA | [3] DEVOLUÇÃO | [4] ROLLOUT: ").strip()
opcao_tecnico = input("Testemunha 1: [1] Padrão | [2] Digitar E-mail: ").strip()
email_testemunha_1 = EMAIL_TESTEMUNHA_1 if opcao_tecnico != "2" else input("E-mail: ").strip()

email_testemunha_2 = EMAIL_TESTEMUNHA_3 if tipo_termo == "4" else EMAIL_TESTEMUNHA_2

if tipo_termo == "4":
    busca_chave_antigo = input("\nID Equipamento Antigo: ").strip()
    busca_serial_novo = input("Serial Equipamento Novo: ").strip()
else:
    busca_chave = input("\nID Equipamento/Usuário: ").strip()

pasta_perfil = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PerfilRPA")
options = Options()
options.add_experimental_option("detach", True)
options.add_argument(f"user-data-dir={pasta_perfil}")
options.add_argument("--start-maximized")

driver = webdriver.Edge(options=options)
driver.maximize_window()
wait = WebDriverWait(driver, 20)

driver.get(URL_SISTEMA)
time.sleep(3)

def preencher_manual(chave):
    return {
        "modelo": "Notebook Padrão", "serial": chave, "patrimonio": "00000", 
        "hostname": chave, "nome_colab": "Colaborador", "matricula": "000000",
        "area": "TI", "tipo_raw": "Notebook"
    }

ativos_para_processar = []

if tipo_termo == "1":
    ativo = extrair_ativos_itsm(driver, wait, busca_chave)
    ativos_para_processar.append({"tipo_doc": "Onboarding", "prefixo_titulo": "Termo_ONB", "template_url": URL_TPL_1, "ativo": ativo[0] if ativo else preencher_manual(busca_chave)})
elif tipo_termo == "2":
    ativo_novo = preencher_manual("NOVO")
    ativo_antigo = preencher_manual("ANTIGO")
    ativos_para_processar.append({"tipo_doc": "Entrega", "prefixo_titulo": "Termo_ENT", "template_url": URL_TPL_2, "ativo": ativo_novo})
    ativos_para_processar.append({"tipo_doc": "Devolução", "prefixo_titulo": "Termo_DEV", "template_url": URL_TPL_3, "ativo": ativo_antigo})
elif tipo_termo == "3":
    ativo = extrair_ativos_itsm(driver, wait, busca_chave)
    ativos_para_processar.append({"tipo_doc": "Devolução", "prefixo_titulo": "Termo_DEV", "template_url": URL_TPL_3, "ativo": ativo[0] if ativo else preencher_manual(busca_chave)})
elif tipo_termo == "4":
    ativo_novo = preencher_manual(busca_serial_novo)
    ativo_antigo = preencher_manual(busca_chave_antigo)
    ativos_para_processar.append({"tipo_doc": "Entrega", "prefixo_titulo": "Termo_ENT", "template_url": URL_TPL_2, "ativo": ativo_novo})
    ativos_para_processar.append({"tipo_doc": "Devolução", "prefixo_titulo": "Termo_DEV", "template_url": URL_TPL_3, "ativo": ativo_antigo})

if tipo_termo == "3":
    email_recebedor = input("👉 E-mail do Responsável: ").strip().lower()
else:
    email_recebedor = prever_email_colaborador(ativos_para_processar[0]["ativo"]["nome_colab"])

agora = datetime.now()

for item in ativos_para_processar:
    ativo = item["ativo"]
    nome_doc = f"{item['prefixo_titulo']}_{empresa_rotulo}_{limpar_nome_arquivo(ativo['nome_colab'])}"
    dados_dinamicos = {
        "{{NOME_COLAB}}": ativo["nome_colab"].upper(), "{{MATRICULA}}": ativo["matricula"].upper(),
        "{{HOSTNAME}}": ativo["hostname"].upper(), "{{MODELO}}": ativo["modelo"],
        "{{DATA}}": agora.strftime("%d/%m/%Y"), "{{VALOR}}": VALOR_PADRAO
    }
    executar_fluxo_docs(driver, wait, item["template_url"], nome_doc, dados_dinamicos, tipo_empresa, email_recebedor, EMAIL_TESTEMUNHA_1, EMAIL_TESTEMUNHA_2, item["tipo_doc"])

print("\n🎉 EXECUÇÃO FINALIZADA!")