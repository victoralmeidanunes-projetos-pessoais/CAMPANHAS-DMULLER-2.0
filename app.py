# =========================================
# IMPORTS
# =========================================
# Importa bibliotecas e módulos necessários para o aplicativo Streamlit.
import streamlit as st
from PIL import Image
from streamlit_pdf_viewer import pdf_viewer
import os
from datetime import datetime, timedelta

from db_config import (
    validar_login,
    registrar_acesso,
    conectar,
    conectar_supabase,
    criar_tabela,
    listar_acessos,
    listar_logs_envio_email
)

from funções import (
    renderizar_tela_acessos,
    renderizar_tela_historico_atualizacoes,
    renderizar_tela_logs_envio_email,
    renderizar_tela_pagamentos_campanhas,
)


# =========================================
# BANCO
# =========================================
# Inicializa as tabelas necessárias no banco local antes de carregar o app.
criar_tabela()

# =========================================
# LOGIN
# =========================================
# Controla o estado de autenticação do usuário na sessão Streamlit.

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "perfil" not in st.session_state:
    st.session_state.perfil = ""

def tela_login():
    # Exibe a tela de login e valida credenciais usando o banco de dados.
    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.image("imagens/LOGO LOGIN.png", width=250)

    



    

    st.title("🔐 Login")

    login = st.text_input("Usuário")

    senha = st.text_input(
        "Senha",
        type="password"
    )

    if st.button("Entrar"):

        usuario = validar_login(login, senha)

        if usuario:

            

            st.session_state.logado = True
            st.session_state.usuario = usuario[1]
            st.session_state.perfil = usuario[2]

            supabase = conectar_supabase()
            registrar_acesso(
                supabase,
                usuario[1]
            )

            st.rerun()

        else:

            st.error(
                "USUÁRIO OU SENHA INVÁLIDOS"
            )


# =========================================
# BLOQUEIO DO APP
# =========================================
# Bloqueia o restante da aplicação enquanto o usuário não estiver autenticado.

if not st.session_state.logado:

    tela_login()

    st.stop()


# =========================================
# CONFIG
# =========================================

st.set_page_config(
    page_title="CAMPANHAS",
    layout="wide", 
    page_icon="📊"
)

PASTA_RAIZ = "MECÂNICAS"

EXT_IMAGEM = [".png", ".jpg", ".jpeg", ".webp"]
EXT_PDF = [".pdf"]
EXT_EXCEL = [".xlsx", ".xlsb", ".xlsm"]

# =========================================
# CSS
# =========================================
# Aplica estilos personalizados ao layout do Streamlit.

st.markdown("""
<style>
html, body, [class*="css"] {
    background: radial-gradient(circle at top left, #e8f1ff 0%, #f5f8ff 30%, #ffffff 100%);
    color: #111827;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

.stApp {
    min-height: 100vh;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d254d 0%, #07162d 100%);
    color: #f8fafc;
}

.block-container {
    padding: 1.5rem 1.5rem 2rem;
}

.stButton>button {
    background-color: #0b63ce;
    color: white;
    border-radius: 0.85rem;
    border: none;
    padding: 0.8rem 1.15rem;
    transition: background-color 0.2s ease;
}

.stButton>button:hover {
    background-color: #094fa1;
}

[data-testid="stSidebar"] .sidebar-user {
    margin-bottom: 0.65rem;
    padding: 0.85rem 1rem;
    border-radius: 0.95rem;
    background: rgba(255,255,255,0.08);
    color: #ffffff !important;
}

.logo-container {
    background: transparent;
    padding: 0;
    margin-bottom: 0.6rem;
    border-radius: 0.85rem;
}

.sidebar-card {
    background: transparent;
    border: none;
    border-radius: 0.85rem;
    padding: 0;
    margin-bottom: 0.6rem;
    box-shadow: none;
}

.streamlit-expanderHeader {
    border-radius: 1rem !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 1rem;
    background: rgba(255,255,255,0.88);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6 {
    color: #ffffff !important;
}

.stMarkdown > div > p {
    line-height: 1.65;
}

.hero-card {
    padding: 1.4rem 1.4rem 1.45rem;
    background: rgba(255,255,255,0.95);
    border-radius: 1.25rem;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.06);
    margin-bottom: 1.5rem;
}

.metric-card {
    background: #ffffff;
    border-radius: 1.05rem;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(15, 23, 42, 0.08);
}

@media (max-width: 768px) {
    .hero-card {
        padding: 1.2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================
# LOGO
# =========================================
# Carrega o logotipo exibido na barra lateral do aplicativo.

logo = Image.open("imagens/logo.png")

# =========================================
# SIDEBAR
# =========================================
# Gera o painel lateral com informações do usuário e controles de filtro.

with st.sidebar:

    st.markdown(
        "<div class='logo-container sidebar-card'>",
        unsafe_allow_html=True
    )

    st.image(
        logo,
        use_container_width=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # ==========================
    # USUÁRIO LOGADO
    # ==========================

    st.markdown(
        "<div class='sidebar-card'>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='sidebar-card-title'>Perfil de acesso</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='sidebar-user'>👤  {st.session_state.usuario}</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='sidebar-user'>🔑  {st.session_state.perfil}</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )



# =========================================
# CONTADORES
# =========================================
# Conta PDFs disponíveis por pauta e fornecedor para exibir o resumo inicial.

contagem_pautas = {}
fornecedores_por_pauta = {}

if os.path.exists(PASTA_RAIZ):

    for pauta in sorted(os.listdir(PASTA_RAIZ)):

        caminho_pauta = os.path.join(PASTA_RAIZ, pauta)

        if not os.path.isdir(caminho_pauta):
            continue

        total_pdf = 0
        lista_fornecedores = []

        for fornecedor in sorted(os.listdir(caminho_pauta)):

            caminho_fornecedor = os.path.join(
                caminho_pauta,
                fornecedor
            )

            if not os.path.isdir(caminho_fornecedor):
                continue

            quantidade = 0

            for arq in os.listdir(caminho_fornecedor):

                if arq.startswith("~$"):
                    continue

                if arq.lower().endswith(".pdf"):
                    quantidade += 1

            total_pdf += quantidade

            lista_fornecedores.append(
                (fornecedor, quantidade)
            )

        contagem_pautas[pauta] = total_pdf

        fornecedores_por_pauta[pauta] = (
            lista_fornecedores
        )

# =========================================
# CABEÇALHO
# =========================================
# Mostra título e resumo geral dos CAMPANHAS ATIVAS.

st.markdown(
    """
    <div class='hero-card'>
        <div style='display:flex; flex-wrap:wrap; gap:1rem; align-items:center; justify-content:space-between;'>
            <div style='min-width:260px;'>
                <h1 style='margin-bottom:0.25rem; font-size:2.65rem; color:#0f172a;'>CAMPANHAS ATIVAS</h1>
                <p style='margin:0; color:#475569; font-size:1rem;'>Painel moderno para navegar, filtrar e acessar seus CAMPANHAS rapidamente.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================
# RESUMO
# =========================================
# Exibe um expander com estatísticas por pauta e fornecedor.
for pauta, lista in fornecedores_por_pauta.items():

    total = contagem_pautas[pauta]

    with st.expander(f"📁 {pauta} | {total} CAMPANHAS", expanded=False):

        st.markdown(f"""
        <div style="
            background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
            padding: 1rem;
            border-radius: 1rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
            margin-bottom: 0.85rem;">
            <div style='font-weight:700; color:#0f172a;'>📁 {pauta} | {total} CAMPANHAS</div>
            <div style='color:#475569; margin-top:0.25rem;'>Fornecedores listados: {len(lista)}</div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(7)

        for i, (fornecedor, qtd) in enumerate(lista):

            with cols[i % 7]:
                st.info(f"{fornecedor}: {qtd}")



st.divider()

# =========================================
# FILTROS
# =========================================
# Painel lateral de seleção de pauta, fornecedor e pesquisa.

pautas = sorted([
    p for p in os.listdir(PASTA_RAIZ)
    if os.path.isdir(os.path.join(PASTA_RAIZ, p))
])

st.sidebar.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sidebar-card-title'>Filtros de pesquisa</div>", unsafe_allow_html=True)

pauta_sel = st.sidebar.selectbox(
    "Pauta",
    ["Todas"] + pautas
)

lista_pautas = (
    pautas if pauta_sel == "Todas"
    else [pauta_sel]
)

fornecedores = []

for p in lista_pautas:

    caminho_pauta = os.path.join(
        PASTA_RAIZ,
        p
    )

    for f in os.listdir(caminho_pauta):

        caminho_f = os.path.join(
            caminho_pauta,
            f
        )

        if os.path.isdir(caminho_f):

            fornecedores.append(f)

fornecedores = sorted(set(fornecedores))

fornecedor_sel = st.sidebar.selectbox(
    "Fornecedor",
    ["Todos"] + fornecedores
)

pesquisa = st.sidebar.text_input(
    "Pesquisar"
)

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# =========================================
# ABAS
# =========================================
# Define as abas principais visíveis no app de acordo com o perfil do usuário.

if st.session_state.perfil == "ADMINISTRADOR MASTER":

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 MECÂNICAS",
        "📊 CAMPANHAS",
        "🔐 ACESSOS",
        "🕛 ATUALIZAÇÕES",
        "📧 LOGS ENVIO EMAIL",
        "💵 PAGAMENTOS CAMPANHAS"
    ])

else:

    tab1, tab2, tab4, tab6 = st.tabs([
        "📄 MECÂNICAS",
        "📊 CAMPANHAS",
        "🕛 ATUALIZAÇÕES",
        "💵 PAGAMENTOS CAMPANHAS"
    ])

contador = 0

# =========================================
# TAB PDFs
# =========================================
# Lista e exibe PDFs das mecânicas incluindo visualização e download.

with tab1:

    for p in lista_pautas:

        caminho_pauta = os.path.join(
            PASTA_RAIZ,
            p
        )

        if not os.path.isdir(caminho_pauta):
            continue

        for f in os.listdir(caminho_pauta):

            if (
                fornecedor_sel != "Todos"
                and f != fornecedor_sel
            ):
                continue

            pasta = os.path.join(
                caminho_pauta,
                f
            )

            if not os.path.isdir(pasta):
                continue

            arquivos = sorted(
                os.listdir(pasta),
                reverse=True
            )

            for arq in arquivos:

                if arq.startswith("~$"):
                    continue

                if not arq.lower().endswith(".pdf"):
                    continue

                if (
                    pesquisa
                    and pesquisa.lower()
                    not in arq.lower()
                ):
                    continue

                contador += 1

                caminho = os.path.join(
                    pasta,
                    arq
                )

                st.markdown(f"## {f}")
                st.caption(p)

                pdf_viewer(
                    caminho,
                    width="100%",
                    height=800,
                    key=f"{p}_{f}_{arq}"
                )

                with open(caminho, "rb") as file:

                    st.download_button(
                        "📥 Baixar PDF",
                        file,
                        file_name=arq
                    )

                st.divider()

# =========================================
# TAB IMAGENS
# =========================================
# Mostra previews de imagens de mecânicas e permite download de Excel relacionado.

with tab2:

    for p in lista_pautas:

        caminho_pauta = os.path.join(
            PASTA_RAIZ,
            p
        )

        if not os.path.isdir(caminho_pauta):
            continue

        for f in os.listdir(caminho_pauta):

            if (
                fornecedor_sel != "Todos"
                and f != fornecedor_sel
            ):
                continue

            pasta = os.path.join(
                caminho_pauta,
                f)

            if not os.path.isdir(pasta):
                continue

            arquivos = sorted(
                os.listdir(pasta),
                reverse=True
            )


            previews_exibidos = set()

            for arq in arquivos:

                if arq.startswith("~$"):
                    continue

                nome_lower = arq.lower()

                # SOMENTE PREVIEW
                if "_preview" not in nome_lower:
                    continue

                if not nome_lower.endswith(".png"):
                    continue

                nome_base = nome_lower.replace(
                    "_preview.png",
                    ""
                )

                if nome_base in previews_exibidos:
                    continue

                previews_exibidos.add(nome_base)

                caminho_preview = os.path.join(
                    pasta,
                    arq
                )

                st.markdown(f"## {f}")
                st.caption(p)

                st.image(
                    caminho_preview,
                    use_container_width=True
                )

                # =====================================
                # EXCEL RELACIONADO
                # =====================================

                excel_relacionado = None

                for arquivo_excel in arquivos:

                    if arquivo_excel.startswith("~$"):
                        continue

                    nome_excel = os.path.splitext(
                        arquivo_excel
                    )[0].lower()

                    ext_excel = os.path.splitext(
                        arquivo_excel
                    )[1].lower()

                    if ext_excel not in EXT_EXCEL:
                        continue

                    if nome_excel == nome_base:

                        excel_relacionado = os.path.join(
                            pasta,
                            arquivo_excel
                        )

                        break

                # =====================================
                # BOTÃO DOWNLOAD EXCEL
                # =====================================

                if excel_relacionado:

                    with open(
                        excel_relacionado,
                        "rb"
                    ) as file_excel:

                        st.download_button(
                            label="📥 Baixar Excel",
                            data=file_excel,
                            file_name=os.path.basename(
                                excel_relacionado
                            ),
                            mime="application/vnd.ms-excel"
                        )

                st.divider()

# =========================================
# TAB HISTÓRICO DE ACESSOS
# =========================================
# Exibe os registros de acessos via Supabase para administradores.


if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab3:
        renderizar_tela_acessos()


# =========================================
# TAB LOGS ENVIO EMAIL
# =========================================
# Exibe logs de envio de email do banco local para administradores.

if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab5:
        renderizar_tela_logs_envio_email()


# =========================================
# TAB CAMPANHAS
# =========================================
# Exibe a tabela CAMPANHAS armazenada em usuarios.db para administradores.

if st.session_state.perfil == "ADMINISTRADOR MASTER" or st.session_state.perfil == "SUPERVISOR":

    with tab6:
        renderizar_tela_pagamentos_campanhas()


# =========================================
# TAB HISTÓRICO DE ATT
# =========================================
# Exibe o histórico de atualizações de arquivos carregados no sistema.


with tab4:
    renderizar_tela_historico_atualizacoes()
# =========================================
# FOOTER
# =========================================


st.sidebar.write(
    f"CAMPANHAS: {contador}"
)