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


from db_config import BANCO, registrar_log_envio_email, garantir_colunas_fornecedores

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
    garantir_colunas_fornecedores()

    fornecedor_normalizado = _normalizar_texto(fornecedor)

    conn = sqlite3.connect(BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT fornecedor, email_destinatario, XLSX, PNG, PDF FROM fornecedores")
    linhas = cursor.fetchall()
    conn.close()

    for nome, emails, xlsx, png, pdf in linhas:
        if nome is None or emails is None:
            continue
        if _normalizar_texto(nome) == fornecedor_normalizado:
            return (
                emails,
                _normalizar_flag(xlsx, default=1),
                _normalizar_flag(png, default=1),
                _normalizar_flag(pdf, default=0)
            )

    return None, 1, 1, 0


def _normalizar_flag(valor, default: int) -> int:
    if valor is None:
        return default
    if isinstance(valor, int):
        return 1 if valor == 1 else 0
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in {"1", "true", "sim", "s", "yes"}:
            return 1
        return 0
    try:
        return 1 if int(valor) == 1 else 0
    except Exception:
        return default


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


def _encontrar_pdf_para_png(caminho_png: str) -> str | None:
    caminho_png = os.path.abspath(caminho_png)
    pasta = Path(caminho_png).parent
    nome_base = Path(caminho_png).stem

    candidato = pasta / f"{nome_base}.pdf"
    if candidato.exists():
        return str(candidato)

    raiz = Path(__file__).resolve().parent
    candidato = raiz / f"{nome_base}.pdf"
    if candidato.exists():
        return str(candidato)

    for arquivo in raiz.rglob(f"{nome_base}.pdf"):
        return str(arquivo)

    return None


def enviar_email_fornecedor_por_png(caminho_png: str) -> bool:
    caminho_png = os.path.abspath(caminho_png)
    fornecedor = Path(caminho_png).parent.name
    destinatarios, enviar_xlsx, enviar_png, enviar_pdf = _buscar_destinatarios(fornecedor)

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

    arquivo_excel = None
    if enviar_xlsx:
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

    arquivo_pdf = None
    if enviar_pdf:
        arquivo_pdf = _encontrar_pdf_para_png(caminho_png)
        if arquivo_pdf is None:
            erro_texto = f"Não foi possível localizar o arquivo PDF com o mesmo nome de {caminho_png}."
            _log_envio("pdf_nao_encontrado", caminho_png, destinatarios, erro=erro_texto)
            registrar_log_envio_email(
                arquivo_png=caminho_png,
                arquivo_excel=arquivo_excel,
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

    <p>Olá! Segue atualização do acompanhamento:</p>

    {f'<p><img src="cid:{cid_img}" width="1000"></p>' if enviar_png else '<p>O corpo do e-mail não inclui o preview em PNG.</p>'}

    {f'<p>Arquivo Excel anexado: <b>{Path(arquivo_excel).name}</b></p>' if enviar_xlsx and arquivo_excel else ''}
    {f'<p>Arquivo PDF anexado: <b>{Path(arquivo_pdf).name}</b></p>' if enviar_pdf and arquivo_pdf else ''}

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

    if enviar_png:
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

    if enviar_xlsx and arquivo_excel:
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

    # PDF anexado

    if enviar_pdf and arquivo_pdf:
        with open(arquivo_pdf, "rb") as f:

            anexo_pdf = MIMEApplication(f.read())

            anexo_pdf.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(
                    arquivo_pdf
                )
            )

            msg.attach(anexo_pdf)

    

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
