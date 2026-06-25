import os
import sqlite3
from pathlib import Path

import win32com.client as win32

from db_config import BANCO

EXCEL_EXTS = [".xlsx", ".xlsb", ".xlsm"]


def _normalizar_texto(texto: str) -> str:
    return texto.strip().lower()


def _buscar_destinatarios(fornecedor: str):
    fornecedor_normalizado = _normalizar_texto(fornecedor)

    conn = sqlite3.connect(BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT fornecedor, email_destinatario FROM fornecedores")
    linhas = cursor.fetchall()
    conn.close()

    for nome, emails in linhas:
        if nome is None or emails is None:
            continue
        if _normalizar_texto(nome) == fornecedor_normalizado:
            return emails

    return None


def _encontrar_excel_para_png(caminho_png: str) -> str | None:
    caminho_png = os.path.abspath(caminho_png)
    pasta = Path(caminho_png).parent
    nome_base = Path(caminho_png).stem

    # Procura na mesma pasta pelo mesmo nome com extensão Excel
    for ext in EXCEL_EXTS:
        candidato = pasta / f"{nome_base}{ext}"
        if candidato.exists():
            return str(candidato)

    # Procura também dentro do projeto atual
    raiz = Path(__file__).resolve().parent
    for ext in EXCEL_EXTS:
        for arquivo in raiz.rglob(f"{nome_base}{ext}"):
            return str(arquivo)

    return None


def enviar_email_fornecedor_por_png(caminho_png: str) -> bool:
    caminho_png = os.path.abspath(caminho_png)
    fornecedor = Path(caminho_png).parent.name
    destinatarios = _buscar_destinatarios(fornecedor)

    if not destinatarios:
        return False

    arquivo_excel = _encontrar_excel_para_png(caminho_png)
    if arquivo_excel is None:
        raise FileNotFoundError(
            f"Não foi possível localizar o arquivo Excel com o mesmo nome de {caminho_png}."
        )

    outlook = win32.Dispatch("Outlook.Application")
    mensagem = outlook.CreateItem(0)

    mensagem.To = destinatarios
    mensagem.Subject = f"Atualização: {Path(caminho_png).name}"
    mensagem.BodyFormat = 2

    # Anexa o Excel e o PNG
    mensagem.Attachments.Add(arquivo_excel)
    anexos = mensagem.Attachments
    anexo_png = anexos.Add(caminho_png)

    try:
        property_accessor = anexo_png.PropertyAccessor
        property_accessor.SetProperty(
            "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
            "updatedpng"
        )
    except Exception:
        pass

    mensagem.HTMLBody = (
        "<p>O arquivo PNG atualizado está abaixo:</p>"
        f"<p><img src=\"cid:updatedpng\" alt=\"Imagem atualizada\"></p>"
        f"<p>Arquivo Excel anexado: {Path(arquivo_excel).name}</p>"
    )

    mensagem.Send()
    return True
