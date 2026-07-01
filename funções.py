import re
import unicodedata
from datetime import datetime, timedelta

import streamlit as st

from db_config import conectar, listar_acessos, listar_logs_envio_email
from historico import listar_atualizacoes_periodo, listar_ultimas_atualizacoes


@st.cache_data
def carregar_campanhas():
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM CAMPANHAS")
        linhas = cursor.fetchall()
        colunas = [descricao[0] for descricao in cursor.description]
    except Exception as exc:
        conn.close()
        raise RuntimeError(
            f"Falha ao carregar CAMPANHAS de usuarios.db: {exc}"
        ) from exc
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return colunas, linhas


def _normalizar_texto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


@st.cache_data
def carregar_soma_premiados_por_campanha(equipe=None):
    try:
        conn = conectar()
        cursor = conn.cursor()
        if equipe is None:
            cursor.execute("SELECT CAMPANHA, SUM([VALOR R$]) FROM PREMIADOS GROUP BY CAMPANHA")
        else:
            cursor.execute(
                "SELECT CAMPANHA, SUM([VALOR R$]) FROM PREMIADOS WHERE UPPER(TRIM(EQUIPE)) = UPPER(TRIM(?)) GROUP BY CAMPANHA",
                (equipe,),
            )
        rows = cursor.fetchall()
    except Exception:
        return {}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {str(r[0]).strip(): (r[1] or 0) for r in rows}


@st.cache_data
def carregar_premiados_da_equipe(equipe):
    if not equipe:
        return []

    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT CAMPANHA, [VALOR R$], EQUIPE FROM PREMIADOS WHERE UPPER(TRIM(EQUIPE)) = UPPER(TRIM(?))",
            (equipe,),
        )
        rows = cursor.fetchall()
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return rows


@st.cache_data
def preparar_dados_campanhas(colunas, linhas, soma_premiados):
    excluir = {"ID", "id", "ORIGEM", "origem", "DESTINO", "destino"}

    campanha_col = next((c for c in colunas if c.upper() == "CAMPANHA"), None)
    data_pagamento_col = next(
        (
            c
            for c in colunas
            if c.upper().replace(" ", "_") in {"DATA_PAGAMENTO", "DATADEPGTO", "DATAPAGAMENTO", "PAGAMENTO"}
        ),
        None,
    )
    status_col = next((c for c in colunas if c.upper() == "STATUS"), None)
    fornecedor_col = next((c for c in colunas if c.upper() == "FORNECEDOR"), None)

    dados_campanhas = []
    for linha in linhas:
        registro = {colunas[i]: valor for i, valor in enumerate(linha) if colunas[i] not in excluir}

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

    return dados_campanhas, campanha_col, data_pagamento_col, status_col, fornecedor_col


@st.cache_data
def filtrar_dados_campanhas(
    dados_campanhas,
    status_col,
    fornecedor_col,
    data_pagamento_col,
    status_sel,
    fornecedor_sel,
    selecao_data,
):
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
            mes_ano = str(registro.get(data_pagamento_col, "")).strip().upper()
            if mes_ano not in selecao_data:
                continue

        registros_filtrados.append(registro)

    return registros_filtrados


@st.cache_data
def carregar_premiados_relacionados(campanhas_visiveis, equipe=None):
    if not campanhas_visiveis:
        return [], []

    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PREMIADOS)")
        info = cursor.fetchall()
        prem_cols = [c[1] for c in info] if info else []

        placeholders = ",".join(["?" for _ in campanhas_visiveis])
        if equipe is None:
            cursor.execute(
                f"SELECT * FROM PREMIADOS WHERE CAMPANHA IN ({placeholders})",
                tuple(campanhas_visiveis),
            )
        else:
            cursor.execute(
                f"SELECT * FROM PREMIADOS WHERE CAMPANHA IN ({placeholders}) AND UPPER(TRIM(EQUIPE)) = UPPER(TRIM(?))",
                tuple(campanhas_visiveis) + (equipe,),
            )
        prem_rows = cursor.fetchall()
    except Exception:
        return [], []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    premiados_data = [
        {prem_cols[i]: val for i, val in enumerate(row)}
        for row in prem_rows
    ] if prem_cols else []

    return premiados_data, prem_cols


@st.cache_data
def formatar_valor_brl(val):
    try:
        valor = float(val)
    except Exception:
        return val

    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _normalizar_coluna(valor):
    if valor is None:
        return ""
    texto = str(valor)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]", "", texto.upper())


def _converter_para_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    texto = texto.replace("R$", "").replace("r$", "").replace(" ", "").strip()
    texto = re.sub(r"[^0-9,\.-]", "", texto)
    if texto == "" or texto in ["-", ".", ","]:
        return 0.0

    try:
        if texto.count(",") == 1 and texto.count(".") >= 1:
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", ".")
        return float(texto)
    except Exception:
        try:
            return float(texto)
        except Exception:
            return 0.0


@st.cache_data(ttl=120)
def carregar_acessos_periodo(data_inicio=None, data_fim=None):
    acessos = listar_acessos(data_inicio=data_inicio, data_fim=data_fim)
    dados = []

    for registro in acessos:
        if "data_hora" in registro and isinstance(registro["data_hora"], str):
            try:
                registro["data_hora"] = datetime.fromisoformat(registro["data_hora"]).strftime("%d/%m/%Y %H:%M")
            except ValueError:
                pass

        dados.append(registro)

    return dados


@st.cache_data(ttl=60)
def carregar_logs_envio_periodo(data_inicio=None, data_fim=None):
    logs = listar_logs_envio_email(data_inicio=data_inicio, data_fim=data_fim)
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
        status_icon = "✅" if any(term in status_lower for term in ["sucesso", "success", "ok", "enviado"]) else "❌"

        display_logs.append({
            "nome_arquivo": registro.get("nome_arquivo", ""),
            "destinatário": registro.get("destinatario_email", ""),
            "status": status_icon,
            "data_hora": data_hora,
            "arquivo_xlsx": "✅" if registro.get("arquivo_excel", 0) == 1 else "❌",
            "arquivo_png": "✅" if registro.get("arquivo_png", 0) == 1 else "❌",
            "arquivo_pdf": "✅" if registro.get("arquivo_pdf", 0) == 1 else "❌",
        })

    return display_logs


@st.cache_data(ttl=60)
def carregar_historico_atualizacoes(tipo_visualizacao="Ver últimas", data_inicio=None, data_fim=None):
    if tipo_visualizacao == "Ver últimas":
        atualizacoes = listar_ultimas_atualizacoes()
    else:
        atualizacoes = listar_atualizacoes_periodo(data_inicio, data_fim)

    return [
        {"Arquivo": arquivo, "Data/Hora": data_hora}
        for arquivo, data_hora in atualizacoes
    ]


def renderizar_tela_acessos():
    st.title("🔐 Acessos")

    tipo_visualizacao_acessos = st.radio(
        "Visualização",
        ["ACESSOS NO MÊS", "OUTRAS DATAS"],
        horizontal=True,
    )

    try:
        if tipo_visualizacao_acessos == "ACESSOS NO MÊS":
            inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
            fim_mes = datetime.now()

            with st.spinner("Calculando acessos do mês..."):
                acessos = carregar_acessos_periodo(inicio_mes, fim_mes)
        else:
            coluna_inicio, coluna_fim = st.columns(2)
            data_inicio = coluna_inicio.date_input(
                "Data inicial",
                datetime.now().date() - timedelta(days=30),
                key="acessos_data_inicio",
            )
            data_final = coluna_fim.date_input(
                "Data final",
                datetime.now().date(),
                key="acessos_data_final",
            )

            if data_inicio > data_final:
                st.error("Data inicial não pode ser maior que a data final.")
                acessos = []
            else:
                inicio = datetime.combine(data_inicio, datetime.min.time())
                fim = datetime.combine(data_final, datetime.max.time())

                with st.spinner("Calculando acessos entre as datas..."):
                    acessos = carregar_acessos_periodo(inicio, fim)

        if acessos:
            st.dataframe(acessos, use_container_width=True)
        else:
            st.info("Nenhum acesso encontrado no período.")

    except Exception as exc:
        st.error(f"Não foi possível carregar os acessos: {exc}")


def renderizar_tela_logs_envio_email():
    st.title("📧 Logs de Envio de Email")

    tipo_visualizacao_logs = st.radio(
        "Visualização",
        ["ENVIOS NO MÊS", "OUTRAS DATAS"],
        horizontal=True,
    )

    try:
        if tipo_visualizacao_logs == "ENVIOS NO MÊS":
            inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
            fim_mes = datetime.now()

            with st.spinner("Calculando logs de envio do mês..."):
                logs = carregar_logs_envio_periodo(inicio_mes, fim_mes)
        else:
            coluna_inicio, coluna_fim = st.columns(2)
            data_inicio = coluna_inicio.date_input(
                "Data inicial",
                datetime.now().date() - timedelta(days=30),
                key="logs_envio_data_inicio",
            )
            data_final = coluna_fim.date_input(
                "Data final",
                datetime.now().date(),
                key="logs_envio_data_final",
            )

            if data_inicio > data_final:
                st.error("Data inicial não pode ser maior que a data final.")
                logs = []
            else:
                inicio = datetime.combine(data_inicio, datetime.min.time())
                fim = datetime.combine(data_final, datetime.max.time())

                with st.spinner("Calculando logs de envio entre as datas..."):
                    logs = carregar_logs_envio_periodo(inicio, fim)

        if logs:
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("Nenhum envio encontrado no período.")

    except Exception as exc:
        st.error(f"Não foi possível carregar os logs de envio: {exc}")


def renderizar_tela_historico_atualizacoes():
    st.title("🕛 Histórico de Atualizações")

    tipo_visualizacao = st.radio(
        "Visualização",
        ["Ver últimas", "Ver mais"],
        horizontal=True,
    )

    dados = []

    if tipo_visualizacao == "Ver últimas":
        with st.spinner("Calculando histórico de atualizações..."):
            dados = carregar_historico_atualizacoes("Ver últimas")
    else:
        tipo_periodo_atualizacao = st.radio(
            "Filtrar por período",
            ["ATUALIZAÇÕES NO MÊS", "OUTRAS DATAS"],
            horizontal=True,
        )

        if tipo_periodo_atualizacao == "ATUALIZAÇÕES NO MÊS":
            inicio_mes = datetime(datetime.now().year, datetime.now().month, 1)
            fim_mes = datetime.now()

            with st.spinner("Calculando histórico de atualizações do mês..."):
                dados = carregar_historico_atualizacoes("Ver mais", inicio_mes, fim_mes)
        else:
            coluna_inicio, coluna_fim = st.columns(2)
            data_inicio = coluna_inicio.date_input(
                "Data inicial",
                datetime.now().date() - timedelta(days=30),
                key="atualizacoes_data_inicio",
            )
            data_final = coluna_fim.date_input(
                "Data final",
                datetime.now().date(),
                key="atualizacoes_data_final",
            )

            if data_inicio > data_final:
                st.error("Data inicial não pode ser maior que a data final.")
                dados = []
            else:
                inicio = datetime.combine(data_inicio, datetime.min.time())
                fim = datetime.combine(data_final, datetime.max.time())

                with st.spinner("Calculando histórico de atualizações entre as datas..."):
                    dados = carregar_historico_atualizacoes("Ver mais", inicio, fim)

    if dados:
        st.dataframe(dados, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma atualização registrada.")


def renderizar_tela_pagamentos_campanhas():
    st.title("💵 PAGAMENTOS CAMPANHAS")

    try:
        perfil = st.session_state.get("perfil", "")
        usuario_logado = st.session_state.get("usuario", "")
        is_admin_master = perfil == "ADMINISTRADOR MASTER"
        equipe_filtrada = None if is_admin_master else usuario_logado

        colunas, linhas = carregar_campanhas()
        soma_premiados = carregar_soma_premiados_por_campanha(equipe_filtrada)
        dados_campanhas, campanha_col, data_pagamento_col, status_col, fornecedor_col = preparar_dados_campanhas(
            colunas,
            linhas,
            soma_premiados,
        )

        if not is_admin_master and campanha_col:
            campanhas_equipe = {
                str(registro[0]).strip()
                for registro in carregar_premiados_da_equipe(equipe_filtrada)
                if registro and registro[0] is not None
            }
            dados_campanhas = [
                registro
                for registro in dados_campanhas
                if str(registro.get(campanha_col, "")).strip() in campanhas_equipe
            ]

        status_padrao = "ABERTA"
        status_options = [status_padrao]
        if status_col:
            status_values = sorted(
                {
                    str(registro.get(status_col, "")).strip()
                    for registro in dados_campanhas
                    if registro.get(status_col) is not None
                }
            )
            status_options = [status_padrao] + [s for s in status_values if s.upper() != status_padrao]
        else:
            status_col = None

        fornecedor_options = ["Todos"]
        if fornecedor_col:
            fornecedor_values = sorted(
                {
                    str(registro.get(fornecedor_col, "")).strip()
                    for registro in dados_campanhas
                    if registro.get(fornecedor_col)
                }
            )
            fornecedor_options = ["Todos"] + fornecedor_values

        coluna_f1, coluna_f2, coluna_f3 = st.columns(3)

        with coluna_f1:
            status_sel = st.selectbox("Status", status_options, index=0)

        with coluna_f2:
            fornecedor_sel = st.selectbox("Fornecedor", fornecedor_options, index=0)

        with coluna_f3:
            if data_pagamento_col:
                valores_data = []
                for registro in dados_campanhas:
                    valor = registro.get(data_pagamento_col)
                    if valor:
                        valores_data.append(str(valor).strip().upper())

                meses_ano = sorted(set(valores_data), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))
                meses_ano = [f for f in meses_ano if f]
                selecao_data = st.multiselect(
                    "Data pagamento (mês/ano)",
                    meses_ano,
                    default=[],
                    help="Selecione um ou mais meses/anos de pagamento",
                )
            else:
                st.markdown(
                    "<div style='margin-top: 1rem; color:#6b7280;'>Nenhuma coluna de data de pagamento encontrada.</div>",
                    unsafe_allow_html=True,
                )
                selecao_data = []

        metrics_placeholder = st.container()

        registros_filtrados = filtrar_dados_campanhas(
            dados_campanhas,
            status_col,
            fornecedor_col,
            data_pagamento_col,
            status_sel,
            fornecedor_sel,
            selecao_data,
        )

        if registros_filtrados:
            total_disponibilizado = 0.0
            for registro in registros_filtrados:
                valor = registro.get("DISPONIBILIZADO", 0)
                try:
                    if valor is None:
                        valor = 0
                    if isinstance(valor, str):
                        valor = (
                            valor.replace("R$", "")
                            .replace(".", "")
                            .replace(",", ".")
                            .strip()
                        )
                    total_disponibilizado += float(valor)
                except Exception:
                    pass

            totals_fornecedor = {}
            for registro in registros_filtrados:
                fornecedor_val = registro.get(fornecedor_col, "") if fornecedor_col else ""
                key = str(fornecedor_val).strip() if fornecedor_val is not None else ""
                total_p = registro.get("Total Premiados (R$)", 0)
                try:
                    num = float(total_p)
                except Exception:
                    num = 0.0
                totals_fornecedor[key] = totals_fornecedor.get(key, 0.0) + num

            tabela_fornecedores = [
                {
                    "FORNECEDOR": k if k else "(sem fornecedor)",
                    "Total Premiados (R$)": formatar_valor_brl(v),
                }
                for k, v in sorted(totals_fornecedor.items(), key=lambda item: item[0])
            ]

            with st.expander("🧾 Totais por fornecedor", expanded=False):
                st.dataframe(tabela_fornecedores, use_container_width=True)

            with st.expander("🗂️ Campanhas filtradas", expanded=False):
                st.markdown("<h3 style='text-align:center'>🗂️ Campanhas filtradas</h3>", unsafe_allow_html=True)
                regs_display = []
                for registro in registros_filtrados:
                    rr = registro.copy()
                    if "Total Premiados (R$)" in rr:
                        try:
                            rr["Total Premiados (R$)"] = formatar_valor_brl(rr["Total Premiados (R$)"])
                        except Exception:
                            pass
                    regs_display.append(rr)

                st.dataframe(regs_display, use_container_width=True)

            if campanha_col:
                campanhas_visiveis = sorted(
                    {
                        str(registro.get(campanha_col, "")).strip()
                        for registro in registros_filtrados
                        if registro.get(campanha_col)
                    }
                )
                if campanhas_visiveis:
                    premiados_data, prem_cols = carregar_premiados_relacionados(
                        campanhas_visiveis,
                        equipe_filtrada,
                    )

                    total_valor = 0.0
                    unique_campaigns = len(campanhas_visiveis)
                    unique_cod = 0
                    percentual_utilizado = 0.0

                    if premiados_data:
                        with st.expander("🏆 Premiados — relacionados às campanhas visíveis", expanded=False):
                            st.markdown("---")
                            st.subheader("Premiados — relacionados às campanhas visíveis")

                            try:
                                import pandas as pd

                                df = pd.DataFrame(premiados_data)
                                df_display = df.copy()

                                code_col = None
                                name_col = None
                                camp_col = None
                                valor_col_local = None
                                for coluna in prem_cols:
                                    coluna_norm = _normalizar_coluna(coluna)
                                    if code_col is None and "COD" in coluna_norm and "PESSOA" in coluna_norm:
                                        code_col = coluna
                                    if name_col is None and "NOME" in coluna_norm:
                                        name_col = coluna
                                    if camp_col is None and ("CAMPANHA" in coluna_norm or "CAMPAIGN" in coluna_norm):
                                        camp_col = coluna
                                    if valor_col_local is None and "VALOR" in coluna_norm:
                                        valor_col_local = coluna

                                if valor_col_local and camp_col and code_col and len(df) > 0:
                                    total_valor = df[valor_col_local].apply(_converter_para_float).sum()
                                    unique_campaigns = int(df[camp_col].nunique())
                                    unique_cod = int(df[code_col].nunique())

                                    if total_disponibilizado > 0:
                                        percentual_utilizado = total_valor / total_disponibilizado

                                if valor_col_local and valor_col_local in df_display.columns:
                                    df_display[valor_col_local] = df_display[valor_col_local].apply(
                                        lambda valor: formatar_valor_brl(_converter_para_float(valor)) if valor not in [None, ""] else ""
                                    )

                                def destacar_duplicadas(df_):
                                    matriz = pd.DataFrame("", index=df_.index, columns=df_.columns)
                                    for coluna in df_.columns:
                                        try:
                                            duplicadas = df_[coluna].duplicated(keep=False)
                                        except Exception:
                                            duplicadas = pd.Series([False] * len(df_))
                                        matriz.loc[duplicadas, coluna] = "background-color: #cfe8ff"
                                    return matriz

                                st.write(df_display.style.apply(destacar_duplicadas, axis=None))

                                if code_col and name_col and camp_col and valor_col_local:
                                    pivot_df = df.copy()
                                    pivot_df[valor_col_local] = pivot_df[valor_col_local].apply(_converter_para_float)

                                    agg = pivot_df.groupby([code_col, camp_col])[valor_col_local].sum().reset_index()
                                    pt = agg.pivot_table(
                                        index=code_col,
                                        columns=camp_col,
                                        values=valor_col_local,
                                        aggfunc="sum",
                                        fill_value=0,
                                    ).reset_index()

                                    names = pivot_df.groupby(code_col)[name_col].agg(
                                        lambda x: next((str(v) for v in x if pd.notna(v) and str(v).strip() != ""), "")
                                    ).reset_index()
                                    pt = pt.merge(names, on=code_col, how="left")

                                    campaign_cols = [c for c in pt.columns if c not in [code_col, name_col]]
                                    ordered = [code_col, name_col] + campaign_cols
                                    pt = pt[ordered]
                                    pt["TOTAL (R$)"] = pt[campaign_cols].sum(axis=1)

                                    for c in campaign_cols:
                                        pt[c] = pt[c].apply(lambda x: formatar_valor_brl(x) if x and x != 0 else "")
                                    pt["TOTAL (R$)"] = pt["TOTAL (R$)"].apply(lambda x: formatar_valor_brl(x) if x and x != 0 else "")

                                    st.markdown("---")
                                    st.subheader("Batalha naval por cód_pessoa × campanha (valores pagos)")
                                    st.dataframe(pt, use_container_width=True)
                                else:
                                    st.info("Não foi possível gerar a visualização pivô: colunas necessárias não encontradas (cód_pessoa, nome, campanha, valor).")

                            except Exception as exc:
                                st.error(f"Erro gerando visualizações de premiados: {exc}")
                    else:
                        st.info("Nenhum premiado encontrado para as campanhas visíveis.")

                    metrics_cols = metrics_placeholder.columns(5)
                    metrics_cols[0].metric("🏦 Total Disponibilizado", formatar_valor_brl(total_disponibilizado))
                    metrics_cols[1].metric("💰 Total Premiados (filtrados)", formatar_valor_brl(total_valor))
                    metrics_cols[2].metric("📈 % Utilizado", f"{percentual_utilizado:.2f}%".replace(".", ","))
                    metrics_cols[3].metric("📁 Campanhas únicas", unique_campaigns)
                    metrics_cols[4].metric("👥 Cód. pessoa únicos", unique_cod)
                else:
                    st.info("Nenhuma campanha encontrada entre os registros filtrados.")
            else:
                st.markdown("<div style='margin-top: 0.5rem; color:#6b7280;'>Coluna 'CAMPANHA' não encontrada na tabela de campanhas; não é possível filtrar PREMIADOS.</div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum registro encontrado com os filtros selecionados.")

    except Exception as exc:
        st.error(f"Não foi possível carregar as campanhas: {exc}")
