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



from supabase import create_client
import streamlit as st

@st.cache_resource
def conectar_supabase():
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

