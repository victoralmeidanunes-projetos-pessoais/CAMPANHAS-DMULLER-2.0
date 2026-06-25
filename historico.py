import sqlite3
import os
from datetime import datetime
import streamlit as st

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BANCO = os.path.join(BASE_DIR, "historico.db")


def conectar():
    return sqlite3.connect(BANCO)


def criar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_atualizacoes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            arquivo TEXT NOT NULL,

            data_hora DATETIME

        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_historico_data_hora ON historico_atualizacoes(data_hora)"
    )

    conn.commit()
    conn.close()


def registrar_atualizacao(arquivo):

    data_hora = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO historico_atualizacoes
        (
            arquivo,
            data_hora
        )
        VALUES (?, ?)
    """, (
        arquivo,data_hora
    ))

    conn.commit()
    conn.close()



def listar_atualizacoes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            arquivo,
            data_hora
        FROM historico_atualizacoes
        ORDER BY id DESC
    """)

    dados = cursor.fetchall()

    print(
        f"LISTANDO {len(dados)} ATUALIZAÇÕES"
    )

    conn.close()

    return dados

def listar_atualizacoes_periodo(data_inicio, data_fim):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            arquivo,
            data_hora
        FROM historico_atualizacoes
        WHERE data_hora BETWEEN ? AND ?
        ORDER BY data_hora DESC
    """,
    (
        data_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        data_fim.strftime("%Y-%m-%d %H:%M:%S")
    ))

    dados = cursor.fetchall()

    conn.close()

    return dados


def listar_ultimas_atualizacoes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            h.arquivo,
            h.data_hora
        FROM historico_atualizacoes h
        INNER JOIN (
            SELECT
                arquivo,
                MAX(data_hora) AS ultima_data
            FROM historico_atualizacoes
            GROUP BY arquivo
        ) ult
            ON h.arquivo = ult.arquivo
            AND h.data_hora = ult.ultima_data
        ORDER BY h.data_hora DESC
    """)

    dados = cursor.fetchall()

    conn.close()

    return dados
