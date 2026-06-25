# =========================================
# IMPORTS
# =========================================

import streamlit as st
from PIL import Image
from streamlit_pdf_viewer import pdf_viewer
import os

from db_config import (
    validar_login,
    registrar_acesso,
    conectar_supabase,
    criar_tabela
)

from historico import (listar_atualizacoes,listar_ultimas_atualizacoes)

# =========================================
# BANCO
# =========================================

criar_tabela()

# =========================================
# LOGIN
# =========================================


if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "perfil" not in st.session_state:
    st.session_state.perfil = ""

def tela_login():

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

if not st.session_state.logado:

    tela_login()

    st.stop()


# =========================================
# CONFIG
# =========================================

st.set_page_config(
    page_title="Campanhas",
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

st.markdown("""
<style>
            
[data-testid="stSidebar"] div[data-testid="stAlert"][kind="success"] {
    background-color: #003366 !important;
    color: #00ffcc !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] div[data-testid="stAlert"][kind="info"] {
    background-color: #002244 !important;
    color: #ffd000 !important;
    border-radius: 10px !important;
}

html, body, [class*="css"] {
    background-color: #f5f5f5;
    color: #131203;
}
            

.block-container {
    padding: 1rem 2rem;
}

[data-testid="stSidebar"] {
    background: #012060;
}

.logo-container {
    background: rgba(255,255,255,0.08);
    padding: 0px;
    margin-bottom: 1px;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: white !important;
}

[data-testid="stSidebar"] h1 {
    color: white !important;
}
            


</style>
""", unsafe_allow_html=True)

# =========================================
# LOGO
# =========================================

logo = Image.open("imagens/logo.png")

# =========================================
# SIDEBAR
# =========================================

with st.sidebar:

    st.markdown(
        "<div class='logo-container'>",
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

    st.success(
    f"👤  {st.session_state.usuario}")

    st.info(
    f"🔑  {st.session_state.perfil}")



# =========================================
# CONTADORES
# =========================================

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
st.text(" ")

st.header("CAMPANHAS ATIVAS")

st.caption(
    f"{sum(contagem_pautas.values())} campanhas ativas"
)

# =========================================
# RESUMO
# =========================================
for pauta, lista in fornecedores_por_pauta.items():

    total = contagem_pautas[pauta]

    with st.expander(f"📁 {pauta} | {total} campanhas", expanded=False):

        st.markdown(f"""
        <div style="
            background:#A8B9DC;
            padding:2px;
            border-radius:2px;
            text-align:center;
            color:white;
            font-weight:500;
            margin-bottom:8px;">
            📁 {pauta} | {total} campanhas
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

pautas = sorted([
    p for p in os.listdir(PASTA_RAIZ)
    if os.path.isdir(os.path.join(PASTA_RAIZ, p))
])

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

# =========================================
# ABAS
# =========================================

if st.session_state.perfil == "ADMINISTRADOR MASTER":

    tab1, tab2, tab3, tab4= st.tabs([
        "📄 MECÂNICAS",
        "📊 ACOMPANHAMENTOS",
        "🔐 ACESSOS",
        "🕛 ATUALIZAÇÕES"
    ])

else:

    tab1, tab2 = st.tabs([
        "📄 MECÂNICAS",
        "📊 ACOMPANHAMENTOS"
    ])

contador = 0

# =========================================
# TAB PDFs
# =========================================

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


if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab3:

        st.title("🔐 PÁGINA EM DESENVOLVIMENTO")

        

# =========================================
# TAB HISTÓRICO DE ATT
# =========================================


if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab4:

        st.title("🕛 Histórico de Atualizações")

        tipo_visualizacao = st.radio(
            "Visualização",
            [
                "Ver últimas",
                "Ver todas"
            ],
            horizontal=True
        )

        if tipo_visualizacao == "Ver últimas":

            atualizacoes = listar_ultimas_atualizacoes()

        else:

            atualizacoes = listar_atualizacoes()

        if atualizacoes:

            dados = []

            for arquivo, data_hora in atualizacoes:

                dados.append({
                    "Arquivo": arquivo,
                    "Data/Hora": data_hora
                })

            st.dataframe(
                dados,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Nenhuma atualização registrada."
            )
# =========================================
# FOOTER
# =========================================

st.sidebar.divider()

st.sidebar.write(
    f"CAMPANHAS: {contador}"
)