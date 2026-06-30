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

from historico import (listar_atualizacoes,listar_ultimas_atualizacoes, listar_atualizacoes_periodo)

# =========================================
# BANCO
# =========================================
# Inicializa as tabelas necessárias no banco local antes de carregar o app.
criar_tabela()


def carregar_campanhas():
    # usa a conexão local SQLite do usuarios.db para carregar a tabela CAMPANHAS
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM CAMPANHAS")
        linhas = cursor.fetchall()
        colunas = [descricao[0] for descricao in cursor.description]
    except Exception as exc:
        conn.close()
        raise RuntimeError(
            "Falha ao carregar CAMPANHAS de usuarios.db: "
            f"{exc}"
        ) from exc

    conn.close()

    return colunas, linhas

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
    page_title="Acompanhamentos",
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
# Mostra título e resumo geral dos acompanhamentos ativos.

st.markdown(
    """
    <div class='hero-card'>
        <div style='display:flex; flex-wrap:wrap; gap:1rem; align-items:center; justify-content:space-between;'>
            <div style='min-width:260px;'>
                <h1 style='margin-bottom:0.25rem; font-size:2.65rem; color:#0f172a;'>ACOMPANHAMENTOS ATIVOS</h1>
                <p style='margin:0; color:#475569; font-size:1rem;'>Painel moderno para navegar, filtrar e acessar seus acompanhamentos rapidamente.</p>
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

    with st.expander(f"📁 {pauta} | {total} acompanhamentos", expanded=False):

        st.markdown(f"""
        <div style="
            background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
            padding: 1rem;
            border-radius: 1rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
            margin-bottom: 0.85rem;">
            <div style='font-weight:700; color:#0f172a;'>📁 {pauta} | {total} acompanhamentos</div>
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
        "📊 ACOMPANHAMENTOS",
        "🔐 ACESSOS",
        "🕛 ATUALIZAÇÕES",
        "📧 LOGS ENVIO EMAIL",
        "🗂️ CAMPANHAS"
    ])

else:

    tab1, tab2, tab4 = st.tabs([
        "📄 MECÂNICAS",
        "📊 ACOMPANHAMENTOS",
        "🕛 ATUALIZAÇÕES"
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

        st.title("🔐 Acessos")

        tipo_visualizacao_acessos = st.radio(
            "Visualização",
            [
                "ACESSOS NO MÊS",
                "OUTRAS DATAS"
            ],
            horizontal=True
        )

        try:
            if tipo_visualizacao_acessos == "ACESSOS NO MÊS":
                inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
                fim_mes = datetime.now()

                with st.spinner("Calculando acessos do mês..."):
                    acessos = listar_acessos(
                        data_inicio=inicio_mes,
                        data_fim=fim_mes
                    )

                    if acessos:
                        for registro in acessos:
                            if "data_hora" in registro and isinstance(registro["data_hora"], str):
                                try:
                                    registro["data_hora"] = datetime.fromisoformat(registro["data_hora"]).strftime("%d/%m/%Y %H:%M")
                                except ValueError:
                                    pass

                        st.dataframe(
                            acessos,
                            use_container_width=True
                        )
                    else:
                        st.info("Nenhum acesso encontrado no período.")

            else:
                coluna_inicio, coluna_fim = st.columns(2)
                data_inicio = coluna_inicio.date_input(
                    "Data inicial",
                    datetime.now().date() - timedelta(days=30),
                    key="acessos_data_inicio"
                )
                data_final = coluna_fim.date_input(
                    "Data final",
                    datetime.now().date(),
                    key="acessos_data_final"
                )

                if data_inicio > data_final:
                    st.error("Data inicial não pode ser maior que a data final.")
                    acessos = []
                else:
                    inicio = datetime.combine(data_inicio, datetime.min.time())
                    fim = datetime.combine(data_final, datetime.max.time())

                    with st.spinner("Calculando acessos entre as datas..."):
                        acessos = listar_acessos(
                            data_inicio=inicio,
                            data_fim=fim
                        )

                        if acessos:
                            for registro in acessos:
                                if "data_hora" in registro and isinstance(registro["data_hora"], str):
                                    try:
                                        registro["data_hora"] = datetime.fromisoformat(registro["data_hora"]).strftime("%d/%m/%Y %H:%M")
                                    except ValueError:
                                        pass

                            st.dataframe(
                                acessos,
                                use_container_width=True
                            )
                        else:
                            st.info("Nenhum acesso encontrado no período.")

        except Exception as e:
            st.error(f"Não foi possível carregar os acessos: {e}")


# =========================================
# TAB LOGS ENVIO EMAIL
# =========================================
# Exibe logs de envio de email do banco local para administradores.

if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab5:

        st.title("📧 Logs de Envio de Email")

        tipo_visualizacao_logs = st.radio(
            "Visualização",
            [
                "ENVIOS NO MÊS",
                "OUTRAS DATAS"
            ],
            horizontal=True
        )

        try:
            if tipo_visualizacao_logs == "ENVIOS NO MÊS":
                inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
                fim_mes = datetime.now()

                with st.spinner("Calculando logs de envio do mês..."):
                    logs = listar_logs_envio_email(
                        data_inicio=inicio_mes,
                        data_fim=fim_mes
                    )
            else:
                coluna_inicio, coluna_fim = st.columns(2)
                data_inicio = coluna_inicio.date_input(
                    "Data inicial",
                    datetime.now().date() - timedelta(days=30),
                    key="logs_envio_data_inicio"
                )
                data_final = coluna_fim.date_input(
                    "Data final",
                    datetime.now().date(),
                    key="logs_envio_data_final"
                )

                if data_inicio > data_final:
                    st.error("Data inicial não pode ser maior que a data final.")
                    logs = []
                else:
                    inicio = datetime.combine(data_inicio, datetime.min.time())
                    fim = datetime.combine(data_final, datetime.max.time())

                    with st.spinner("Calculando logs de envio entre as datas..."):
                        logs = listar_logs_envio_email(
                            data_inicio=inicio,
                            data_fim=fim
                        )

            if logs:
                display_logs = []

                for registro in logs:
                    data_hora = registro.get("data_hora", "")
                    if isinstance(data_hora, str):
                        try:
                            data_hora = datetime.fromisoformat(data_hora).strftime("%d/%m/%Y %H:%M")
                        except ValueError:
                            pass

                    status_text = str(registro.get("status", "")).strip()
                    status_lower = status_text.lower()
                    status_icon = "✅" if any(
                        term in status_lower
                        for term in ["sucesso", "success", "ok", "enviado"]
                    ) else "❌"

                    display_logs.append({
                        "nome_arquivo": registro.get("nome_arquivo", ""),
                        "destinatário": registro.get("destinatario_email", ""),
                        "status": status_icon,
                        "data_hora": data_hora,
                        "arquivo_xlsx": "✅" if registro.get("arquivo_excel", 0) == 1 else "❌",
                        "arquivo_png": "✅" if registro.get("arquivo_png", 0) == 1 else "❌",
                        "arquivo_pdf": "✅" if registro.get("arquivo_pdf", 0) == 1 else "❌"
                    })
                st.dataframe(
                    display_logs,
                    use_container_width=True
                )
            else:
                st.info("Nenhum envio encontrado no período.")

        except Exception as e:
            st.error(f"Não foi possível carregar os logs de envio: {e}")


# =========================================
# TAB CAMPANHAS
# =========================================
# Exibe a tabela CAMPANHAS armazenada em usuarios.db para administradores.

if st.session_state.perfil == "ADMINISTRADOR MASTER":

    with tab6:

        st.title("🗂️ Campanhas")

        try:
            colunas, linhas = carregar_campanhas()

            excluir = {"ID", "id", "ORIGEM", "origem", "DESTINO", "destino"}

            # consulta soma dos premiados por campanha
            try:
                conn_p = conectar()
                cursor_p = conn_p.cursor()
                cursor_p.execute('SELECT CAMPANHA, SUM([VALOR R$]) FROM PREMIADOS GROUP BY CAMPANHA')
                rows_p = cursor_p.fetchall()
            except Exception:
                rows_p = []
            finally:
                try:
                    conn_p.close()
                except Exception:
                    pass

            soma_premiados = {str(r[0]).strip(): (r[1] or 0) for r in rows_p}

            campanha_col = next((c for c in colunas if c.upper() == "CAMPANHA"), None)
            data_pagamento_col = next((c for c in colunas if c.upper().replace(" ", "_") in {"DATA_PAGAMENTO", "DATADEPGTO", "DATAPAGAMENTO", "PAGAMENTO"}), None)

            dados_campanhas = []
            for linha in linhas:
                registro = {colunas[i]: valor for i, valor in enumerate(linha) if colunas[i] not in excluir}

                # obtém valor da coluna campanha para buscar soma
                camp_val = None
                if campanha_col:
                    try:
                        idx = colunas.index(campanha_col)
                        camp_val = linha[idx]
                    except Exception:
                        camp_val = None

                chave = str(camp_val).strip() if camp_val is not None else ""
                total_prem = float(soma_premiados.get(chave, 0) or 0)
                registro["Total Premiados (R$)"] = round(total_prem, 2)

                dados_campanhas.append(registro)

            # iniciais do filtro
            status_padrao = "ABERTA"
            status_col = next((c for c in colunas if c.upper() == "STATUS"), None)
            fornecedor_col = next((c for c in colunas if c.upper() == "FORNECEDOR"), None)

            status_options = [status_padrao]
            if status_col:
                status_values = sorted({str(registro.get(status_col, "")).strip() for registro in dados_campanhas if registro.get(status_col) is not None})
                status_options = [status_padrao] + [s for s in status_values if s.upper() != status_padrao]
            else:
                status_col = None

            fornecedor_options = ["Todos"]
            if fornecedor_col:
                fornecedor_values = sorted({str(registro.get(fornecedor_col, "")).strip() for registro in dados_campanhas if registro.get(fornecedor_col)})
                fornecedor_options = ["Todos"] + fornecedor_values

            coluna_f1, coluna_f2, coluna_f3 = st.columns(3)

            with coluna_f1:
                status_sel = st.selectbox(
                    "Status",
                    status_options,
                    index=0
                )

            with coluna_f2:
                fornecedor_sel = st.selectbox(
                    "Fornecedor",
                    fornecedor_options,
                    index=0
                )

            with coluna_f3:
                if data_pagamento_col:
                    valores_data = []
                    for registro in dados_campanhas:
                        valor = registro.get(data_pagamento_col)
                        data = None
                        if isinstance(valor, datetime):
                            data = valor
                        elif isinstance(valor, str):
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m/%Y", "%Y/%m"]:
                                try:
                                    data = datetime.strptime(valor.strip(), fmt)
                                    break
                                except Exception:
                                    continue
                        if data:
                            valores_data.append(data.strftime("%m/%Y"))

                    meses_ano = sorted(set(valores_data), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))
                    meses_ano = [f for f in meses_ano if f]
                    selecao_data = st.multiselect(
                        "Data pagamento (mês/ano)",
                        meses_ano,
                        default=[],
                        help="Selecione um ou mais meses/anos de pagamento"
                    )
                else:
                    st.markdown("<div style='margin-top: 1rem; color:#6b7280;'>Nenhuma coluna de data de pagamento encontrada.</div>", unsafe_allow_html=True)
                    selecao_data = []

            # placeholder para métricas que devem aparecer logo abaixo dos filtros
            metrics_placeholder = st.container()

            def parse_date(value):
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m/%Y", "%Y/%m"]:
                        try:
                            return datetime.strptime(value.strip(), fmt)
                        except Exception:
                            continue
                return None

            registros_filtrados = []
            for registro in dados_campanhas:
                if status_col and status_sel and status_sel.upper() != "TODOS":
                    valor_status = str(registro.get(status_col, "")).strip()
                    if valor_status.upper() != status_sel.upper():
                        continue

                if fornecedor_col and fornecedor_sel != "Todos":
                    valor_fornecedor = str(registro.get(fornecedor_col, "")).strip()
                    if valor_fornecedor != fornecedor_sel:
                        continue

                if data_pagamento_col and selecao_data:
                    valor_data = parse_date(registro.get(data_pagamento_col))
                    if valor_data is None:
                        continue
                    mes_ano = valor_data.strftime("%m/%Y")
                    if mes_ano not in selecao_data:
                        continue

                registros_filtrados.append(registro)

            if registros_filtrados:
                def fmt_currency_local(val):
                    try:
                        f = float(val)
                    except Exception:
                        return val
                    s = f"{f:,.2f}"
                    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
                    return f"R$ {s}"

                # tabela 1: total por fornecedor (primeira tabela)
                totals_fornecedor = {}
                for r in registros_filtrados:
                    fornecedor_val = r.get(fornecedor_col, '') if fornecedor_col else ''
                    key = str(fornecedor_val).strip() if fornecedor_val is not None else ''
                    total_p = r.get('Total Premiados (R$)', 0)
                    try:
                        num = float(total_p)
                    except Exception:
                        num = 0.0
                    totals_fornecedor[key] = totals_fornecedor.get(key, 0.0) + num

                tabela_fornecedores = [
                    {'FORNECEDOR': k if k else '(sem fornecedor)', 'Total Premiados (R$)': fmt_currency_local(v)}
                    for k, v in sorted(totals_fornecedor.items(), key=lambda x: x[0])
                ]

                with st.expander("🧾 Totais por fornecedor", expanded=False):
                    st.dataframe(tabela_fornecedores, use_container_width=True)

                # tabela 2: campanhas filtradas (exibição)
                with st.expander("🗂️ Campanhas filtradas", expanded=False):
                    st.markdown("<h3 style='text-align:center'>🗂️ Campanhas filtradas</h3>", unsafe_allow_html=True)
                    regs_display = []
                    for r in registros_filtrados:
                        rr = r.copy()
                        if 'Total Premiados (R$)' in rr:
                            try:
                                rr['Total Premiados (R$)'] = fmt_currency_local(rr['Total Premiados (R$)'])
                            except Exception:
                                pass
                        regs_display.append(rr)

                    st.dataframe(regs_display, use_container_width=True)

                # --- exibe premiados relacionados às campanhas visíveis na tabela ---
                if campanha_col:
                    campanhas_visiveis = sorted({str(r.get(campanha_col, "")).strip() for r in registros_filtrados if r.get(campanha_col)})
                    if campanhas_visiveis:
                        try:
                            conn_pr = conectar()
                            cur_pr = conn_pr.cursor()
                            # pegar colunas da tabela PREMIADOS
                            cur_pr.execute("PRAGMA table_info(PREMIADOS)")
                            info = cur_pr.fetchall()
                            prem_cols = [c[1] for c in info] if info else []

                            placeholders = ",".join(["?" for _ in campanhas_visiveis])
                            cur_pr.execute(f"SELECT * FROM PREMIADOS WHERE CAMPANHA IN ({placeholders})", tuple(campanhas_visiveis))
                            prem_rows = cur_pr.fetchall()
                        except Exception as e:
                            st.error(f"Erro ao carregar PREMIADOS: {e}")
                            prem_rows = []
                            prem_cols = []
                        finally:
                            try:
                                conn_pr.close()
                            except Exception:
                                pass

                        premiados_data = [
                            {prem_cols[i]: val for i, val in enumerate(row)}
                            for row in prem_rows
                        ] if prem_cols else []

                        if premiados_data:
                            with st.expander("🏆 Premiados — relacionados às campanhas visíveis", expanded=False):
                                st.markdown("---")
                                st.subheader("Premiados — relacionados às campanhas visíveis")

                                # usar pandas para manipular e destacar duplicatas
                                try:
                                    import pandas as pd
                                    import re

                                    df = pd.DataFrame(premiados_data)

                                    # formatador BRL
                                    def fmt_currency(v):
                                        try:
                                            f = float(v)
                                        except Exception:
                                            return v
                                        s = f"{f:,.2f}"
                                        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
                                        return f"R$ {s}"

                                    # criar uma cópia para exibição; destacar duplicatas com cor (sem alterar valores)
                                    df_display = df.copy()

                                    # detectar colunas relevantes
                                    import unicodedata

                                    def norm(s):
                                        if s is None:
                                            return ''
                                        s = str(s)
                                        s = unicodedata.normalize('NFKD', s)
                                        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
                                        return re.sub(r'[^A-Z0-9]', '', s.upper())

                                    code_col = None
                                    name_col = None
                                    camp_col = None
                                    valor_col_local = None
                                    for c in prem_cols:
                                        nc = norm(c)
                                        if code_col is None and 'COD' in nc and 'PESSOA' in nc:
                                            code_col = c
                                        if name_col is None and 'NOME' in nc:
                                            name_col = c
                                        if camp_col is None and ('CAMPANHA' in nc or 'CAMPAIGN' in nc):
                                            camp_col = c
                                        if valor_col_local is None and 'VALOR' in nc:
                                            valor_col_local = c

                                    def safe_to_float(v):
                                        if v is None:
                                            return 0.0
                                        if isinstance(v, (int, float)):
                                            return float(v)
                                        s = str(v).strip()
                                        s = s.replace('R$', '').replace('r$', '').replace(' ', '').strip()
                                        s = re.sub(r'[^0-9,\.-]', '', s)
                                        if s == '' or s in ['-', '.', ',']:
                                            return 0.0
                                        try:
                                            if s.count(',') == 1 and s.count('.') >= 1:
                                                s = s.replace('.', '').replace(',', '.')
                                            else:
                                                s = s.replace(',', '.')
                                            return float(s)
                                        except Exception:
                                            try:
                                                return float(s)
                                            except Exception:
                                                return 0.0

                                    # métricas principais (baseadas nos PREMIADOS filtrados)
                                    total_valor = 0.0
                                    unique_campaigns = 0
                                    unique_cod = 0
                                    if valor_col_local and camp_col and code_col and len(df) > 0:
                                        total_valor = df[valor_col_local].apply(safe_to_float).sum()
                                        unique_campaigns = int(df[camp_col].nunique())
                                        unique_cod = int(df[code_col].nunique())

                                    # preenche métricas no placeholder criado logo após os filtros
                                    metrics_cols = metrics_placeholder.columns(3)
                                    metrics_cols[0].metric("💰 Total Premiados (filtrados)", fmt_currency(total_valor))
                                    metrics_cols[1].metric("📁 Campanhas únicas", unique_campaigns)
                                    metrics_cols[2].metric("👥 Cód. pessoa únicos", unique_cod)

                                    # formatar colunas de valor para exibição no df_display
                                    if valor_col_local and valor_col_local in df_display.columns:
                                        df_display[valor_col_local] = df_display[valor_col_local].apply(lambda v: fmt_currency(safe_to_float(v)) if v not in [None, ''] else '')

                                    def highlight_dup(df_):
                                        m = pd.DataFrame('', index=df_.index, columns=df_.columns)
                                        for col in df_.columns:
                                            try:
                                                dup = df_[col].duplicated(keep=False)
                                            except Exception:
                                                dup = pd.Series([False] * len(df_))
                                            m.loc[dup, col] = 'background-color: #cfe8ff'
                                        return m

                                    st.write(df_display.style.apply(highlight_dup, axis=None))

                                    # preparar pivot (batalha naval) por cód_pessoa x campanhas
                                    if code_col and name_col and camp_col and valor_col_local:
                                        pivot_df = df.copy()
                                        pivot_df[valor_col_local] = pivot_df[valor_col_local].apply(safe_to_float)

                                        # agregar por cód_pessoa e campanha
                                        agg = pivot_df.groupby([code_col, camp_col])[valor_col_local].sum().reset_index()
                                        pt = agg.pivot_table(
                                            index=code_col,
                                            columns=camp_col,
                                            values=valor_col_local,
                                            aggfunc='sum',
                                            fill_value=0
                                        ).reset_index()

                                        # adicionar nome (primeiro encontrado) por código
                                        names = pivot_df.groupby(code_col)[name_col].agg(lambda x: next((str(v) for v in x if pd.notna(v) and str(v).strip() != ''), '')).reset_index()
                                        pt = pt.merge(names, on=code_col, how='left')

                                        # reorganizar colunas: código, nome, campanhas...
                                        campaign_cols = [c for c in pt.columns if c not in [code_col, name_col]]
                                        ordered = [code_col, name_col] + campaign_cols
                                        pt = pt[ordered]

                                        # calcular total por linha (soma de campanhas)
                                        pt['TOTAL (R$)'] = pt[campaign_cols].sum(axis=1)

                                        # formatar campos de campanha e total para BRL
                                        for c in campaign_cols:
                                            pt[c] = pt[c].apply(lambda x: fmt_currency(x) if x and x != 0 else '')
                                        pt['TOTAL (R$)'] = pt['TOTAL (R$)'].apply(lambda x: fmt_currency(x) if x and x != 0 else '')

                                        st.markdown('---')
                                        st.subheader('Batalha naval por cód_pessoa × campanha (valores pagos)')
                                        st.dataframe(pt, use_container_width=True)
                                    else:
                                        st.info('Não foi possível gerar a visualização pivô: colunas necessárias não encontradas (cód_pessoa, nome, campanha, valor).')

                                except Exception as e:
                                    st.error(f'Erro gerando visualizações de premiados: {e}')
                        else:
                            st.info("Nenhum premiado encontrado para as campanhas visíveis.")
                    else:
                        st.info("Nenhuma campanha encontrada entre os registros filtrados.")
                else:
                    st.markdown("<div style='margin-top: 0.5rem; color:#6b7280;'>Coluna 'CAMPANHA' não encontrada na tabela de campanhas; não é possível filtrar PREMIADOS.</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro encontrado com os filtros selecionados.")

        except Exception as e:
            st.error(f"Não foi possível carregar as campanhas: {e}")


# =========================================
# TAB HISTÓRICO DE ATT
# =========================================
# Exibe o histórico de atualizações de arquivos carregados no sistema.


with tab4:

    st.title("🕛 Histórico de Atualizações")

    tipo_visualizacao = st.radio(
        "Visualização",
        [
            "Ver últimas",
            "Ver mais"
        ],
        horizontal=True
    )

    dados = []

    if tipo_visualizacao == "Ver últimas":
        with st.spinner("Calculando histórico de atualizações..."):
            atualizacoes = listar_ultimas_atualizacoes()

        if atualizacoes:
            for arquivo, data_hora in atualizacoes:
                dados.append({
                    "Arquivo": arquivo,
                    "Data/Hora": data_hora
                })

    else:
        tipo_periodo_atualizacao = st.radio(
            "Filtrar por período",
            [
                "ATUALIZAÇÕES NO MÊS",
                "OUTRAS DATAS"
            ],
            horizontal=True
        )

        if tipo_periodo_atualizacao == "ATUALIZAÇÕES NO MÊS":
            inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
            fim_mes = datetime.now()

            with st.spinner("Calculando histórico de atualizações do mês..."):
                atualizacoes = listar_atualizacoes_periodo(
                    inicio_mes,
                    fim_mes
                )

        else:
            coluna_inicio, coluna_fim = st.columns(2)
            data_inicio = coluna_inicio.date_input(
                "Data inicial",
                datetime.now().date() - timedelta(days=30),
                key="atualizacoes_data_inicio"
            )
            data_final = coluna_fim.date_input(
                "Data final",
                datetime.now().date(),
                key="atualizacoes_data_final"
            )

            if data_inicio > data_final:
                st.error("Data inicial não pode ser maior que a data final.")
                atualizacoes = []
            else:
                inicio = datetime.combine(data_inicio, datetime.min.time())
                fim = datetime.combine(data_final, datetime.max.time())

                with st.spinner("Calculando histórico de atualizações entre as datas..."):
                    atualizacoes = listar_atualizacoes_periodo(
                        inicio,
                        fim
                    )

    if atualizacoes:
        for arquivo, data_hora in atualizacoes:
            dados.append({
                "Arquivo": arquivo,
                "Data/Hora": data_hora
            })

    if dados:
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


st.sidebar.write(
    f"ACOMPANHAMENTOS: {contador}"
)