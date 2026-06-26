# db_config.py

import sqlite3
import os
from datetime import datetime

# =========================================
# BANCO
# =========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BANCO = os.path.join(
    BASE_DIR,
    "usuarios.db"
)


def conectar():

    print("\n" + "=" * 70)
    print("BANCO UTILIZADO:")
    print(os.path.abspath(BANCO))
    print("=" * 70 + "\n")

    return sqlite3.connect(BANCO)


# =========================================
# TABELA USUÁRIOS
# =========================================

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


def garantir_coluna_xlsx_fornecedores():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(fornecedores)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if not any(coluna.upper() == "XLSX" for coluna in colunas):
        cursor.execute("ALTER TABLE fornecedores ADD COLUMN XLSX INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


def criar_tabela_fornecedores():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            email_destinatario TEXT,
            XLSX INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()
    garantir_coluna_xlsx_fornecedores()


def criar_tabela_logs_envio_email():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_envio_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            arquivo_png TEXT NOT NULL,
            arquivo_excel TEXT,
            destinatario_email TEXT,
            status TEXT NOT NULL,
            observacao TEXT
        )
    """)

    conn.commit()
    conn.close()


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


def registrar_log_envio_email(arquivo_png, arquivo_excel, destinatario_email, status, observacao=None):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO logs_envio_email
            (data_hora, arquivo_png, arquivo_excel, destinatario_email, status, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            arquivo_png,
            arquivo_excel,
            destinatario_email,
            status,
            observacao
        )
    )

    conn.commit()
    conn.close()


import streamlit as st

@st.cache_resource
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

