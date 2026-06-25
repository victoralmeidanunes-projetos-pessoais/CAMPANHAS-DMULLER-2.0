import os
import sqlite3
from datetime import datetime
from pathlib import Path

import smtplib
import mimetypes

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.utils import make_msgid


from db_config import BANCO, registrar_log_envio_email

EXCEL_EXTS = [".xlsx", ".xlsb", ".xlsm"]
LOG_FILE = Path(__file__).resolve().parent / "envio_email.log"

# CONFIGURAÇÃO SMTP
REMETENTE = "comercial.sc2@dmuller.com.br"
SENHA = "Dmuller.365"
SMTP_SERVER = "smtp.office365.com"
SMTP_PORTA = 587


def _normalizar_texto(texto: str) -> str:
    return texto.strip().lower()


def _log_envio(status: str, caminho_png: str, destinatarios: str | None = None, arquivo_excel: str | None = None, erro: str | None = None) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = (
        f"[{timestamp}] status={status} png={caminho_png} "
        f"destinatarios={destinatarios or 'N/A'} "
        f"excel={arquivo_excel or 'N/A'} "
        f"erro={erro or 'N/A'}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha)


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
        _log_envio("no_destinatario", caminho_png)
        registrar_log_envio_email(
            arquivo_png=caminho_png,
            arquivo_excel=None,
            destinatario_email=None,
            status="fornecedor_nao_encontrado",
            observacao="Fornecedor não encontrado na tabela fornecedores"
        )
        return False

    arquivo_excel = _encontrar_excel_para_png(caminho_png)
    if arquivo_excel is None:
        erro_texto = f"Não foi possível localizar o arquivo Excel com o mesmo nome de {caminho_png}."
        _log_envio("excel_nao_encontrado", caminho_png, destinatarios, erro=erro_texto)
        registrar_log_envio_email(
            arquivo_png=caminho_png,
            arquivo_excel=None,
            destinatario_email=destinatarios,
            status="erro",
            observacao=erro_texto
        )
        raise FileNotFoundError(erro_texto)
    
    msg = MIMEMultipart("related")

    msg["From"] = REMETENTE
    msg["To"] = destinatarios
    msg["Subject"] = f"Atualização: {Path(caminho_png).name}"

    cid_img = make_msgid()[1:-1]

    html = f"""
    <html>
    <body>

    <p>O arquivo atualizado está abaixo:</p>

    <p>
    <img src="cid:{cid_img}" width="1000">
    </p>

    <p>
    Arquivo Excel anexado:
    <b>{Path(arquivo_excel).name}</b>
    </p>

    </body>
    </html>
    """

    alternativo = MIMEMultipart("alternative")

    alternativo.attach(
        MIMEText(
            "Segue atualização da campanha.",
            "plain"
        )
    )

    alternativo.attach(
        MIMEText(
            html,
            "html"
        )
    )

    msg.attach(alternativo)

    # PNG embutido

    with open(caminho_png, "rb") as f:

        imagem = MIMEImage(f.read())

        imagem.add_header(
            "Content-ID",
            f"<{cid_img}>"
        )

        imagem.add_header(
            "Content-Disposition",
            "inline",
            filename=os.path.basename(caminho_png)
        )

        msg.attach(imagem)

    # Excel anexado

    with open(arquivo_excel, "rb") as f:

        anexo = MIMEApplication(f.read())

        anexo.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(
                arquivo_excel
            )
        )

        msg.attach(anexo)

    

    try:

        print("Preparando envio SMTP...")

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORTA
        ) as smtp:

            smtp.starttls()

            smtp.login(
                REMETENTE,
                SENHA
            )

            smtp.send_message(msg)

        print("Email enviado com sucesso!")
    except Exception as e:
        erro_texto = str(e)
        _log_envio("erro_envio", caminho_png, destinatarios, arquivo_excel, erro=erro_texto)
        registrar_log_envio_email(
            arquivo_png=caminho_png,
            arquivo_excel=arquivo_excel,
            destinatario_email=destinatarios,
            status="erro",
            observacao=erro_texto
        )
        raise
