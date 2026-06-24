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



