# pip install watchdog pywin32 pillow
from historico import registrar_atualizacao
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pythoncom
import shutil
import subprocess
import time
import os
from datetime import datetime

from envio_email import enviar_email_fornecedor_por_png
import win32com.client as win32
from PIL import ImageGrab



# ======= CONFIGURAÇÃO GIT HUB =========


PROJETO_DIR = r"B:\Victor\ACOMPANHAMENTOS\PROJETO"

def enviar_git():
    try:
        subprocess.run("git add .", cwd=PROJETO_DIR, shell=True, check=True)

        msg = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        subprocess.run(
            f'git commit -m "{msg}"',
            cwd=PROJETO_DIR,
            shell=True,
            check=True
        )

        subprocess.run("git push", cwd=PROJETO_DIR, shell=True, check=True)

        print("✔ Git atualizado com sucesso!")

    except Exception as e:
        print("❌ Erro no Git:", e)





# ========= CONFIGURAÇÃO =========

ARQUIVOS = [ #KI-PIPOKA
    {
        "origem": r"B:\Victor\PAUTA D\FORNECEDORES PAUTA D\MARCAS PRÓPRIAS\ABERTAS\KIPIPOKA\INCENTIVO KI-PIPOKA JUNINA.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\KIPIPOKA\INCENTIVO KI-PIPOKA JUNINA.xlsx"
    },

    #BITES
    {
        "origem": r"B:\Victor\PAUTA D\FORNECEDORES PAUTA D\MARCAS PRÓPRIAS\ABERTAS\BITES\INCENTIVO BITES - LANÇAMENTOS.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\BITES\INCENTIVO BITES - LANÇAMENTOS.xlsx"
    },

    #CORY

    {
        "origem": r"B:\Anne\7º Acompanhamentos\Cory\CAMPANHA DE INCENTIVO CORY - TRIMESTRAL.xlsx",
        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\CORY\CAMPANHA DE INCENTIVO CORY - TRIMESTRAL.xlsx"
    },

    #SH
    
    {
        "origem": r"B:\Victor\PAUTA M\SANTA HELENA\CAMPANHA SH\CAMPANHA INCENTIVO SH - JUNINA 2026.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\SANTA HELENA\CAMPANHA INCENTIVO SH - JUNINA 2026.xlsx"
    },

    #SH - VESTINDO A CAMISA
    
    {
        "origem": r"B:\Victor\PAUTA M\SANTA HELENA\CAMPANHA SH\INCENTIVO SANTA HELENA - VESTINDO A CAMISA..xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\SANTA HELENA\INCENTIVO SANTA HELENA - VESTINDO A CAMISA..xlsx"
    },

    #YPÊ
    
    {
        "origem": r"B:\Victor\PAUTA M\YPÊ\ABERTAS\Campanha de Incentivo Ypê - Categorias Foco 05'06.xlsb",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\YPÊ\Campanha de Incentivo Ypê - Categorias Foco 05'06.xlsb"
    },

    #FERRERO
    
    #EQUIPE FERRERO
    {
        "origem": r"B:\Victor\PAUTA D\Ferrero\FERRERO\1. ACOMPANHAMENTOS & CAMPANHAS\2026\Ano Fiscal 25'26\CAMPANHAS\3ª SESSIONE\Campanha de incentivo - Equipe Ferrero  25'26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\FERRERO\INCENTIVO EQUIPE FERRERO - SS 3'2026.xlsx"
    },

    #MAESTROS
    {
        "origem": r"B:\Victor\PAUTA D\Ferrero\FERRERO\1. ACOMPANHAMENTOS & CAMPANHAS\2026\Ano Fiscal 25'26\PROJETO MAESTROS\ACOMPANHAMENTOS - MAESTROS FERRERO 25'26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\FERRERO\ACOMPANHAMENTOS - MAESTROS FERRERO 25'26.xlsx"
    },

    #JOHNSON
    
    #TOP CONTAS
    {
        "origem": r"B:\Nicolas\Acompanhamentos\JOHNSON\2025.26\Q4\Campanha Johnson - Top Contas Q4 FY26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\JOHNSON\Campanha Johnson - Top Contas Q4 FY26.xlsx"
    },



    #LOJA PERFEITA

    {
        "origem": r"B:\Nicolas\Acompanhamentos\JOHNSON\2025.26\Q4\Campanha Johnson - Loja Perfeita 360 Q4 FY26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\JOHNSON\Campanha Johnson - Loja Perfeita 360 Q4 FY26.xlsx"
    },

    #PLANO DE NEGÓCIOS / LIDERANÇA

    {
        "origem": r"B:\Nicolas\Acompanhamentos\JOHNSON\2025.26\Q4\Acompanhamento Johnson - Plano de Negócios Q4 FY26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\JOHNSON\INCENTIVO LIDERANÇA - PLANO DE NEGÓCIOS JOHNSON.xlsx"
    },

    #EXPANDINDO

    {
        "origem": r"B:\Nicolas\Acompanhamentos\JOHNSON\2025.26\Q4\Acompanhamento Johnson - Expandindo Q4 FY26.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\JOHNSON\Acompanhamento Johnson - Expandindo Q4 FY26.xlsx"
    },


    #NUTRY

    {
        "origem": r"B:\Victor\PAUTA M\NUTRY\INCENTIVO NUTRY - JUNHO & JULHO.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\NUTRY\INCENTIVO NUTRY - JUNHO & JULHO.xlsx"
    },

#RAYOVAC

    {
        "origem": r"B:\Victor\PAUTA D\FORNECEDORES PAUTA D\Rayovac\CAMPANHAS\VIGENTES\RAYOVAC & ENERGIZER - RANKING JUNHO.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\RAYOVAC\RAYOVAC & ENERGIZER - RANKING JUNHO.xlsx"
    },


#ENERGIZER

    {
        "origem": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\RAYOVAC\RAYOVAC & ENERGIZER - RANKING JUNHO.xlsx",

        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\ENERGIZER\ENERGIZER & RAYOVAC- RANKING JUNHO.xlsx"
    }




    
]



# =====================================

MAPA = {
    os.path.abspath(a["origem"]).lower(): a["destino"]
    for a in ARQUIVOS
}

# =====================================
# GERAR PREVIEW EXCEL
# =====================================

def gerar_preview_excel(caminho_excel):
    pythoncom.CoInitialize()

    try:

        print("\nGerando preview Excel...")

        excel = win32.Dispatch("Excel.Application")

        excel.Visible = False
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(caminho_excel)

        aba = None

        # PROCURA ABA GERAL
        for sheet in wb.Worksheets:

            if "GERAL" in sheet.Name.upper():

                aba = sheet
                break

        # SE NÃO ENCONTRAR
        if aba is None:

            aba = wb.Worksheets(1)

        aba.Activate()

        # ÁREA UTILIZADA
        area = aba.UsedRange

        # COPIA COMO IMAGEM
        area.CopyPicture(Format=2)

        time.sleep(5)

        imagem = ImageGrab.grabclipboard()

        caminho_preview = None
        if imagem:

            caminho_preview = os.path.splitext(
                caminho_excel
            )[0] + ".png"

            imagem.save(caminho_preview)

            print("\nPreview gerado:")
            print(caminho_preview)

        else:

            print("\nNão foi possível gerar preview.")

        wb.Close(False)

        excel.Quit()

        return caminho_preview

    except Exception as e:

        print(f"\nERRO PREVIEW: {e}")

# =====================================
# MONITOR
# =====================================

class MonitorExcel(FileSystemEventHandler):

    ultimo_processamento = {}

    def processar(self, caminho):

        caminho = os.path.abspath(caminho).lower()

        print(f"\nEvento detectado: {caminho}")

        # IGNORA TEMPORÁRIOS
        nome_arquivo = os.path.basename(caminho)

        if nome_arquivo.startswith("~$"):
            return

        if caminho not in MAPA:
            return
        



        # EVITA EVENTOS DUPLICADOS

        agora = time.time()

        ultimo = self.ultimo_processamento.get(
            caminho,
            0)

        if agora - ultimo < 10:

            print(
                "\nEvento duplicado ignorado.")
            

            return

        self.ultimo_processamento[caminho] = agora




        destino = MAPA[caminho]

        try:

            

            os.makedirs(
                os.path.dirname(destino),
                exist_ok=True
            )

            # =================================
            # COPIA EXCEL
            # =================================

            copiado = False

            for tentativa in range(60):

                try:

                    shutil.copy2(
                        caminho,
                        destino
                        )

                    copiado = True

                    break

                except PermissionError:

                    print(
                        f"\nArquivo bloqueado. "
                        f"Tentativa {tentativa+1}/60"
                    )

                time.sleep(1)

            if not copiado:

                print(
                    "\nArquivo não foi liberado "
                    "em 60 segundos."
                )

                return

            print(f"\nCopiado com sucesso:")
            print(caminho)
            print("->")
            print(destino)

            # =================================
            # GERA PREVIEW
            # =================================

            gerar_preview_excel(destino)

            # =================================
            # EXECUTA GITHUB
            # =================================

            print("\nExecutando atualização GitHub...")

            enviar_git()

            print("\nGitHub atualizado com sucesso.\n")

            registrar_atualizacao(
            os.path.basename(destino))



        except Exception as e:

            print(f"\nERRO: {e}")

    # =====================================
    # EVENTOS
    # =====================================

    def on_modified(self, event):

        if event.is_directory:
            return

        caminho = os.path.abspath(event.src_path)

        # IGNORA eventos de PNG gerados pelo preview
        if caminho.lower().endswith(".png"):
            return

        if not caminho.lower().endswith((
            ".xlsx",
            ".xlsb",
            ".xlsm"
        )):
            return

        self.processar(caminho)

    def on_created(self, event):
        if event.is_directory:
            return

        caminho = os.path.abspath(event.src_path)

        if caminho.lower().endswith(".png"):
            try:
                enviado = enviar_email_fornecedor_por_png(caminho)
                if enviado:
                    print(f"Email enviado para fornecedor da pasta: {os.path.basename(os.path.dirname(caminho))}")
                else:
                    print("Fornecedor não encontrado na tabela fornecedores. Nenhum email enviado.")
            except Exception as e:
                print(f"Erro ao enviar email: {e}")
            return

# =====================================
# INICIAR MONITORAMENTO
# =====================================

observer = Observer()

evento = MonitorExcel()

pastas_monitoradas = set()
for a in ARQUIVOS:
    pastas_monitoradas.add(
        os.path.dirname(os.path.abspath(a["origem"]))
    )
    pastas_monitoradas.add(
        os.path.dirname(os.path.abspath(a["destino"]))
    )

for pasta in sorted(pastas_monitoradas):
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)

    print(f"Monitorando pasta:\n{pasta}\n")

    observer.schedule(
        evento,
        pasta,
        recursive=False
    )

observer.start()

print("Monitoramento iniciado...\n")

# =====================================
# LOOP
# =====================================

try:

    while True:

        time.sleep(1)

except KeyboardInterrupt:

    observer.stop()

observer.join()