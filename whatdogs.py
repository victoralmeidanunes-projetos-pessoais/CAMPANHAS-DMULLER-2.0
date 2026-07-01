# pip install watchdog pywin32 pillow
# Importa dependências para monitorar arquivos e processar eventos de sistema.
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime

import pythoncom
import win32com.client as win32
from PIL import ImageGrab
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from db_config import conectar
from envio_email import enviar_email_fornecedor_por_png
from historico import registrar_atualizacao


# =====================================
# CONFIG GIT
# =====================================
# Define o diretório do projeto e as funções que automatizam commits e push no Git.

PROJETO_DIR = r"B:\Victor\ACOMPANHAMENTOS\PROJETO"


def enviar_git():
    try:
        subprocess.run("git add .", cwd=PROJETO_DIR, shell=True, check=True)

        msg = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        subprocess.run(
            f'git commit -m "{msg}"',
            cwd=PROJETO_DIR,
            shell=True,
            check=True,
        )

        subprocess.run("git push", cwd=PROJETO_DIR, shell=True, check=True)

        print("Publicado no GitHub - ✔️")

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Erro ao publicar no GitHub: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Erro ao publicar no GitHub: {exc}") from exc


# =====================================
# ARQUIVOS
# =====================================
# Carrega os caminhos monitorados da tabela CAMPANHAS do banco e converte em um mapeamento de origem/destino.

def carregar_campanhas():
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT ORIGEM, DESTINO FROM CAMPANHAS")
        linhas = cursor.fetchall()
    except Exception as exc:
        conn.close()
        raise RuntimeError(
            "Falha ao carregar CAMPANHAS de usuarios.db: "
            f"{exc}"
        ) from exc

    conn.close()

    arquivos = []
    for origem, destino in linhas:
        if origem is None or destino is None:
            continue
        arquivos.append({
            "origem": origem,
            "destino": destino,
        })

    if not arquivos:
        raise RuntimeError(
            "A tabela CAMPANHAS está vazia ou não possui registros válidos."
        )

    return arquivos


ARQUIVOS = carregar_campanhas()

MAPA = {
    os.path.abspath(a["origem"]).lower(): os.path.abspath(a["destino"])
    for a in ARQUIVOS
}


# =====================================
# PREVIEW EXCEL
# =====================================
# Gera imagem de preview de arquivos Excel usando COM e clipboard.

def gerar_preview_excel(caminho_excel):
    pythoncom.CoInitialize()

    excel = None
    workbook = None

    try:
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        workbook = excel.Workbooks.Open(caminho_excel)

        aba = None
        for sheet in workbook.Worksheets:
            if "GERAL" in sheet.Name.upper():
                aba = sheet
                break

        if aba is None:
            aba = workbook.Worksheets(1)

        aba.Activate()

        area = aba.UsedRange
        area.CopyPicture(Format=2)

        time.sleep(2)

        imagem = ImageGrab.grabclipboard()

        if not imagem:
            raise RuntimeError("não foi possível capturar a imagem da área de transferência")

        caminho_preview = os.path.splitext(caminho_excel)[0] + ".png"
        imagem.save(caminho_preview)

        print("Gerado preview e colocado na pasta - ✔️")
        return caminho_preview

    except Exception as exc:
        raise RuntimeError(f"Erro ao gerar preview: {exc}") from exc
    finally:
        try:
            if workbook is not None:
                workbook.Close(False)
            if excel is not None:
                excel.Quit()
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


# =====================================
# PROCESSAMENTO
# =====================================
# Espera o arquivo ficar liberado para leitura e depois enfileira o processamento.

def esperar_arquivo_liberado(caminho, timeout=60):
    caminho = os.path.abspath(caminho)
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    fim = time.time() + timeout

    while time.time() < fim:
        try:
            with open(caminho, "rb") as handle:
                handle.read(1)

            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(caminho), suffix=".tmp") as tmp:
                    temp_path = tmp.name

                shutil.copy2(caminho, temp_path)
                os.remove(temp_path)
                return True
            except PermissionError:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                time.sleep(0.5)
                continue
            except Exception:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except PermissionError:
            time.sleep(0.5)
        except OSError as exc:
            if time.time() >= fim:
                raise RuntimeError(f"Erro ao ler o arquivo: {exc}") from exc
            time.sleep(0.5)

    raise TimeoutError(f"Arquivo não liberado após {timeout}s: {caminho}")


class MonitorExcel(FileSystemEventHandler):
    def __init__(self, fila):
        super().__init__()
        self.fila = fila
        self._lock = threading.Lock()
        self._pendentes = set()
        self._processando = set()

    def _deve_pular(self, caminho):
        nome = os.path.basename(caminho)
        if nome.startswith("~$"):
            return True
        if nome.lower().endswith(".tmp"):
            return True
        if not caminho.lower().endswith((".xlsx", ".xlsb", ".xlsm")):
            return True
        return False

    def enfileirar(self, caminho):
        caminho = os.path.abspath(caminho).lower()

        if self._deve_pular(caminho):
            return

        if caminho not in MAPA:
            return

        with self._lock:
            if caminho in self._pendentes or caminho in self._processando:
                return
            self._pendentes.add(caminho)

        try:
            esperar_arquivo_liberado(caminho)
            self.fila.put({"caminho": caminho})
            print(f"arquivo enfileirado - {os.path.basename(caminho)}")
        except Exception as exc:
            with self._lock:
                self._pendentes.discard(caminho)
            print(f"Erro ao preparar o arquivo: {exc}")

    def processar_arquivo(self, caminho):
        caminho = os.path.abspath(caminho).lower()
        destino = MAPA.get(caminho)
        nome_arquivo = os.path.basename(caminho)

        if not destino:
            return

        with self._lock:
            self._processando.add(caminho)
            self._pendentes.discard(caminho)

        try:
            os.makedirs(os.path.dirname(destino), exist_ok=True)

            shutil.copy2(caminho, destino)
            print(f"copiado xlsx - ✔️ {nome_arquivo}")

            png = gerar_preview_excel(destino)
            if not png:
                raise RuntimeError("preview não foi gerada")

            enviado = enviar_email_fornecedor_por_png(png)
            if enviado is True:
                print(f"enviado e-mail - ✔️ {nome_arquivo}")
            elif enviado is False:
                print(f"enviado e-mail - ⚠️ {nome_arquivo} (sem destinatário)")
            else:
                print(f"enviado e-mail - ⚠️ {nome_arquivo} (resultado inesperado)")

            enviar_git()
            registrar_atualizacao(os.path.basename(destino))

        except Exception as exc:
            print(f"Erro no processamento de {nome_arquivo}: {exc}")
        finally:
            with self._lock:
                self._processando.discard(caminho)

    def on_created(self, event):
        if event.is_directory:
            return
        self.enfileirar(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.enfileirar(event.src_path)


# =====================================
# START
# =====================================

observer = Observer()
fila = queue.Queue()
evento = MonitorExcel(fila)


def worker_fila():
    while True:
        item = fila.get()
        if item is None:
            fila.task_done()
            break
        evento.processar_arquivo(item["caminho"])
        fila.task_done()


thread_fila = threading.Thread(target=worker_fila, daemon=True)
thread_fila.start()

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
    fila.put(None)
    thread_fila.join(timeout=5)

observer.join()