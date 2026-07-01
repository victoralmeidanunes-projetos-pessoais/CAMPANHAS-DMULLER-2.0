# db_config.py

import sqlite3
import os
from datetime import datetime

# =========================================
# BANCO
# =========================================
# Define o caminho do banco de dados local SQLite e fornece conexão ao arquivo.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BANCO = os.path.join(
    BASE_DIR,
    "usuarios.db"
)

_BANCO_AVISO_EXIBIDO = False


# Abre conexão com o banco SQLite local e exibe o caminho do arquivo.
def conectar():
    global _BANCO_AVISO_EXIBIDO

    if not _BANCO_AVISO_EXIBIDO:
        print("\n" + "=" * 70)
        print("BANCO UTILIZADO:")
        print(os.path.abspath(BANCO))
        print("=" * 70 + "\n")
        _BANCO_AVISO_EXIBIDO = True

    return sqlite3.connect(BANCO)


# =========================================
# TABELA USUÁRIOS
# =========================================
# Cria a tabela de usuários com campos básicos de login e perfil.

def criar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def garantir_colunas_fornecedores():
    # Garante que a tabela de fornecedores contenha colunas de tipo de arquivo.
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(fornecedores)")
    colunas = [coluna[1].upper() for coluna in cursor.fetchall()]

    if "XLSX" not in colunas:
        cursor.execute("ALTER TABLE fornecedores ADD COLUMN XLSX INTEGER DEFAULT 1")

    if "PNG" not in colunas:
        cursor.execute("ALTER TABLE fornecedores ADD COLUMN PNG INTEGER DEFAULT 1")

    if "PDF" not in colunas:
        cursor.execute("ALTER TABLE fornecedores ADD COLUMN PDF INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def criar_tabela_fornecedores():
    # Cria a tabela de fornecedores usada por outros módulos do projeto.
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            email_destinatario TEXT,
            XLSX INTEGER DEFAULT 1,
            PNG INTEGER DEFAULT 1,
            PDF INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    garantir_colunas_fornecedores()


def garantir_colunas_logs_envio_email():
    # Garante que a tabela de logs de envio de email tenha todas as colunas esperadas.
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(logs_envio_email)")
    colunas = [coluna[1].upper() for coluna in cursor.fetchall()]

    if "NOME_ARQUIVO" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN nome_arquivo TEXT")
    if "ARQUIVO_PNG" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN arquivo_png INTEGER NOT NULL DEFAULT 0")
    if "ARQUIVO_EXCEL" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN arquivo_excel INTEGER NOT NULL DEFAULT 0")
    if "ARQUIVO_PDF" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN arquivo_pdf INTEGER NOT NULL DEFAULT 0")
    if "DESTINATARIO_EMAIL" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN destinatario_email TEXT")
    if "STATUS" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN status TEXT NOT NULL DEFAULT ''")
    if "OBSERVACAO" not in colunas:
        cursor.execute("ALTER TABLE logs_envio_email ADD COLUMN observacao TEXT")

    conn.commit()
    conn.close()


def criar_tabela_logs_envio_email():
    # Cria a tabela de logs de envio de email para auditoria e rastreamento.
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_envio_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            nome_arquivo TEXT,
            arquivo_png INTEGER NOT NULL DEFAULT 0,
            arquivo_excel INTEGER NOT NULL DEFAULT 0,
            arquivo_pdf INTEGER NOT NULL DEFAULT 0,
            destinatario_email TEXT,
            status TEXT NOT NULL,
            observacao TEXT
        )
    """)

    conn.commit()
    conn.close()
    garantir_colunas_logs_envio_email()


# =========================================
# USUÁRIOS
# =========================================

def criar_usuario(login, senha, perfil):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO usuarios
            (
                login,
                senha,
                perfil
            )
            VALUES (?, ?, ?)
            """,
            (
                login.strip(),
                senha.strip(),
                perfil.strip()
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:

        print(f"Usuário '{login}' já existe.")

    finally:

        conn.close()


# =========================================
# LOGIN
# =========================================

# Valida as credenciais do usuário e retorna o registro correspondente.
def validar_login(login, senha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            login,
            perfil
        FROM usuarios
        WHERE UPPER(TRIM(login)) = UPPER(?)
        AND TRIM(senha) = ?
        """,
        (
            login.strip(),
            senha.strip()
        )
    )

    usuario = cursor.fetchone()

    conn.close()

    return usuario


# Insere um registro de log de envio de email na tabela logs_envio_email.
def registrar_log_envio_email(nome_arquivo, arquivo_png, arquivo_excel, arquivo_pdf, destinatario_email, status, observacao=None):
    garantir_colunas_logs_envio_email()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO logs_envio_email
            (data_hora, nome_arquivo, arquivo_png, arquivo_excel, arquivo_pdf, destinatario_email, status, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            nome_arquivo,
            1 if arquivo_png else 0,
            1 if arquivo_excel else 0,
            1 if arquivo_pdf else 0,
            destinatario_email,
            status,
            observacao
        )
    )

    conn.commit()
    conn.close()


# Busca registros de logs de envio de email com filtro de datas.
def listar_logs_envio_email(data_inicio=None, data_fim=None):
    conn = conectar()
    cursor = conn.cursor()

    query = "SELECT nome_arquivo, destinatario_email, status, data_hora, arquivo_excel, arquivo_png, arquivo_pdf FROM logs_envio_email"

    conditions = []
    params = []

    if data_inicio is not None:
        conditions.append("data_hora >= ?")
        params.append(data_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    if data_fim is not None:
        conditions.append("data_hora <= ?")
        params.append(data_fim.strftime("%Y-%m-%d %H:%M:%S"))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY data_hora DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "nome_arquivo": row[0],
            "destinatario_email": row[1],
            "status": row[2],
            "data_hora": row[3],
            "arquivo_excel": row[4],
            "arquivo_png": row[5],
            "arquivo_pdf": row[6]
        }
        for row in rows
    ]


import streamlit as st

@st.cache_resource
# Conecta ao Supabase usando as credenciais definidas em st.secrets.
def conectar_supabase():
    try:
        from supabase import create_client
    except ImportError as exc:
        raise ImportError(
            "The supabase package is missing. Add 'supabase' to requirements.txt and redeploy."
        ) from exc

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

from datetime import datetime

def registrar_acesso(supabase, usuario):
    supabase.table("acessos").insert({
        "usuario": usuario,
        "data_hora": datetime.now().isoformat()
    }).execute()


@st.cache_data(ttl=120)
def listar_acessos(data_inicio=None, data_fim=None):
    supabase = conectar_supabase()
    query = supabase.table("acessos").select("usuario, data_hora").order("data_hora", desc=True)

    if data_inicio is not None:
        query = query.gte("data_hora", data_inicio.isoformat())
    if data_fim is not None:
        query = query.lte("data_hora", data_fim.isoformat())

    response = query.execute()

    if hasattr(response, "error") and response.error:
        raise Exception(response.error.message if hasattr(response.error, "message") else str(response.error))

    return response.data or []

