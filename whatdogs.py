# pip install watchdog pywin32 pillow

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pythoncom
import shutil
import subprocess
import time
import os
from datetime import datetime

import win32com.client as win32
from PIL import ImageGrab

from historico import registrar_atualizacao
from envio_email import enviar_email_fornecedor_por_png


# =====================================
# CONFIG GIT
# =====================================

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


# =====================================
# ARQUIVOS
# =====================================

ARQUIVOS = [
    {
        "origem": r"B:\Victor\PAUTA D\FORNECEDORES PAUTA D\MARCAS PRÓPRIAS\ABERTAS\KIPIPOKA\INCENTIVO KI-PIPOKA JUNINA.xlsx",
        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\KIPIPOKA\INCENTIVO KI-PIPOKA JUNINA.xlsx"
    },
    {
        "origem": r"B:\Victor\PAUTA D\FORNECEDORES PAUTA D\MARCAS PRÓPRIAS\ABERTAS\BITES\INCENTIVO BITES - LANÇAMENTOS.xlsx",
        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA D\BITES\INCENTIVO BITES - LANÇAMENTOS.xlsx"
    },
    {
        "origem": r"B:\Anne\7º Acompanhamentos\Cory\CAMPANHA DE INCENTIVO CORY - TRIMESTRAL.xlsx",
        "destino": r"B:\Victor\ACOMPANHAMENTOS\PROJETO\MECÂNICAS\PAUTA M\CORY\CAMPANHA DE INCENTIVO CORY - TRIMESTRAL.xlsx"
    },
]


MAPA = {
    os.path.abspath(a["origem"]).lower(): a["destino"]
    for a in ARQUIVOS
}


# =====================================
# PREVIEW EXCEL
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

        for sheet in wb.Worksheets:
            if "GERAL" in sheet.Name.upper():
                aba = sheet
                break

        if aba is None:
            aba = wb.Worksheets(1)

        aba.Activate()

        area = aba.UsedRange
        area.CopyPicture(Format=2)

        time.sleep(2)

        imagem = ImageGrab.grabclipboard()

        if not imagem:
            print("❌ Falha ao capturar imagem do clipboard")
            wb.Close(False)
            excel.Quit()
            return None

        caminho_preview = os.path.splitext(caminho_excel)[0] + ".png"
        imagem.save(caminho_preview)

        print("✔ Preview gerado:", caminho_preview)

        wb.Close(False)
        excel.Quit()

        return caminho_preview

    except Exception as e:
        print(f"❌ ERRO PREVIEW: {e}")
        return None


# =====================================
# MONITOR
# =====================================

class MonitorExcel(FileSystemEventHandler):

    ultimo_processamento = {}

    def processar(self, caminho):

        caminho = os.path.abspath(caminho).lower()
        print(f"\nEvento detectado: {caminho}")

        nome_arquivo = os.path.basename(caminho)

        if nome_arquivo.startswith("~$"):
            return

        if caminho not in MAPA:
            return

        agora = time.time()
        ultimo = self.ultimo_processamento.get(caminho, 0)

        if agora - ultimo < 10:
            print("Evento duplicado ignorado.")
            return

        self.ultimo_processamento[caminho] = agora

        destino = MAPA[caminho]

        try:
            os.makedirs(os.path.dirname(destino), exist_ok=True)

            # =================================
            # COPIA ARQUIVO
            # =================================

            copiado = False

            for tentativa in range(60):
                try:
                    shutil.copy2(caminho, destino)
                    copiado = True
                    break
                except PermissionError:
                    print(f"Arquivo bloqueado. Tentativa {tentativa+1}/60")
                    time.sleep(1)

            if not copiado:
                print("❌ Arquivo não liberado em 60s")
                return

            print("\n✔ Arquivo copiado")

            # =================================
            # PREVIEW
            # =================================

            png = gerar_preview_excel(destino)

            # =================================
            # EMAIL (AGORA AQUI — CORRETO)
            # =================================

            if png:
                try:
                    print("\nEnviando email fornecedor...")
                    enviado = enviar_email_fornecedor_por_png(png)

                    if enviado:
                        print("✔ Email enviado com sucesso")
                    else:
                        print("⚠ Email não enviado (sem fornecedor)")

                except Exception as e:
                    print("❌ Erro envio email:", e)

            # =================================
            # GIT
            # =================================

            print("\nAtualizando Git...")
            enviar_git()

            registrar_atualizacao(os.path.basename(destino))

        except Exception as e:
            print("❌ ERRO PROCESSAMENTO:", e)


    def on_modified(self, event):

        if event.is_directory:
            return

        caminho = os.path.abspath(event.src_path)

        if caminho.lower().endswith(".png"):
            return

        if not caminho.lower().endswith((".xlsx", ".xlsb", ".xlsm")):
            return

        self.processar(caminho)


# =====================================
# START
# =====================================

observer = Observer()
evento = MonitorExcel()

pastas_monitoradas = set()

for a in ARQUIVOS:
    pastas_monitoradas.add(os.path.dirname(os.path.abspath(a["origem"])))
    pastas_monitoradas.add(os.path.dirname(os.path.abspath(a["destino"])))

for pasta in sorted(pastas_monitoradas):
    os.makedirs(pasta, exist_ok=True)

    print(f"Monitorando: {pasta}")

    observer.schedule(evento, pasta, recursive=False)

observer.start()

print("\nMonitoramento iniciado...\n")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    observer.stop()

observer.join()