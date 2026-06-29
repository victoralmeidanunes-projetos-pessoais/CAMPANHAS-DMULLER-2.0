import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    return sqlite3.connect(DATABASE)


def criar_tabela_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def criar_tabela_log_alteracoes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alteracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tabela TEXT NOT NULL,
            registro_id TEXT,
            coluna TEXT,
            acao TEXT NOT NULL,
            nome_alterador TEXT NOT NULL,
            descricao TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def carregar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tabelas = [linha[0] for linha in cursor.fetchall()]
    conn.close()
    return tabelas


def carregar_colunas(tabela):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [
        {
            "name": linha[1],
            "type": linha[2],
            "notnull": bool(linha[3]),
            "dflt_value": linha[4],
            "pk": bool(linha[5]),
        }
        for linha in cursor.fetchall()
    ]
    conn.close()
    return colunas


def carregar_registros(tabela):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {tabela}")
        registros = cursor.fetchall()
    except sqlite3.OperationalError:
        registros = []
    conn.close()
    return registros


def inserir_log(tabela, registro_id, coluna, acao, nome_alterador, descricao):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alteracoes (data_hora, tabela, registro_id, coluna, acao, nome_alterador, descricao) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tabela,
            str(registro_id) if registro_id is not None else None,
            coluna,
            acao,
            nome_alterador.strip(),
            descricao.strip(),
        ),
    )
    conn.commit()
    conn.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cadastro Caminhos")
        self.geometry("1080x560")
        self.resizable(False, False)

        criar_tabela_usuarios()
        criar_tabela_log_alteracoes()

        self.tabela_selecionada = tk.StringVar()
        self.registro_id = None
        self.colunas_info = []
        self.original_values = []

        self.criar_widgets()
        self.atualizar_tabelas()

    def criar_widgets(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        painel_tabelas = ttk.Frame(self, padding=(10, 10), relief="ridge")
        painel_tabelas.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Label(painel_tabelas, text="Tabelas no banco:").pack(anchor="w")
        self.lista_tabelas = tk.Listbox(painel_tabelas, width=24, height=28, activestyle="dotbox")
        self.lista_tabelas.pack(fill="y", expand=True, pady=(5, 5))
        self.lista_tabelas.bind("<<ListboxSelect>>", self.on_tabela_selecionada)

        ttk.Button(painel_tabelas, text="Atualizar", command=self.atualizar_tabelas).pack(fill="x", pady=(0, 5))
        ttk.Button(painel_tabelas, text="Ver alterações", command=self.ver_alteracoes).pack(fill="x")

        painel_registros = ttk.Frame(self, padding=(0, 10, 10, 10), relief="ridge")
        painel_registros.grid(row=0, column=1, sticky="nsew")
        painel_registros.columnconfigure(0, weight=1)
        painel_registros.rowconfigure(1, weight=1)

        topo = ttk.Frame(painel_registros)
        topo.grid(row=0, column=0, sticky="ew")
        ttk.Label(topo, text="Registros da tabela selecionada:").pack(anchor="w")

        caixa_tree = ttk.Frame(painel_registros)
        caixa_tree.grid(row=1, column=0, sticky="nsew")
        caixa_tree.columnconfigure(0, weight=1)
        caixa_tree.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(caixa_tree, columns=(), show="headings", height=18)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_registro_selecionado)

        barra = ttk.Scrollbar(caixa_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)
        barra.grid(row=0, column=1, sticky="ns")

        self.form_frame = ttk.LabelFrame(self, text="Campos editáveis")
        self.form_frame.grid(row=0, column=2, sticky="ns", padx=(10, 10), pady=(10, 10))
        self.form_frame.columnconfigure(1, weight=1)

        self.campos_frame = ttk.Frame(self.form_frame)
        self.campos_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.entradas = {}
        self.action_fields = {}

        rodape = ttk.Frame(self.form_frame)
        rodape.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        ttk.Button(rodape, text="Inserir", command=lambda: self.abrir_dialogo_acao("inseriu")).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(rodape, text="Salvar", command=lambda: self.abrir_dialogo_acao("editou")).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(rodape, text="Excluir", command=lambda: self.abrir_dialogo_acao("excluiu")).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(rodape, text="Limpar", command=self.limpar_formulario).grid(row=0, column=3, padx=4, pady=4)

        self.status_label = ttk.Label(self, text="Selecione uma tabela para visualizar seus registros.", relief="sunken", anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))

    def atualizar_tabelas(self):
        tabelas = carregar_tabelas()
        self.lista_tabelas.delete(0, tk.END)
        for tabela in tabelas:
            self.lista_tabelas.insert(tk.END, tabela)
        self.status_label.config(text=f"{len(tabelas)} tabela(s) carregada(s). Selecione uma tabela.")
        if tabelas:
            self.lista_tabelas.selection_clear(0, tk.END)
            self.lista_tabelas.selection_set(0)
            self.on_tabela_selecionada()

    def on_tabela_selecionada(self, event=None):
        selecionados = self.lista_tabelas.curselection()
        if not selecionados:
            return
        tabela = self.lista_tabelas.get(selecionados[0])
        self.tabela_selecionada.set(tabela)
        self.carregar_registros_da_tabela()

    def carregar_registros_da_tabela(self):
        tabela = self.tabela_selecionada.get()
        if not tabela:
            return

        self.colunas_info = carregar_colunas(tabela)
        colunas = [coluna["name"] for coluna in self.colunas_info]
        registros = carregar_registros(tabela)

        self.tree.delete(*self.tree.get_children())
        self.tree.config(columns=colunas)

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna)
            self.tree.column(coluna, width=140, anchor="w")

        for registro in registros:
            self.tree.insert("", tk.END, values=registro)

        self.criar_formulario_dinamico()
        self.limpar_formulario()

        self.status_label.config(text=f"Tabela '{tabela}' selecionada. Selecione um registro ou preencha o formulário.")

    def criar_formulario_dinamico(self):
        for widget in self.campos_frame.winfo_children():
            widget.destroy()

        self.entradas = {}
        for idx, coluna in enumerate(self.colunas_info):
            nome = coluna["name"]
            label = ttk.Label(self.campos_frame, text=f"{nome}:")
            label.grid(row=idx, column=0, sticky="e", padx=(0, 6), pady=4)
            entry = ttk.Entry(self.campos_frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=4)
            self.entradas[nome] = entry
            if coluna["pk"] and coluna["type"].upper().startswith("INT"):
                entry.config(state="disabled")

        linha = len(self.colunas_info)
        ttk.Separator(self.campos_frame, orient="horizontal").grid(row=linha, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(self.campos_frame, text="Nome do alterador:").grid(row=linha + 1, column=0, sticky="e", padx=(0, 6), pady=4)
        self.action_fields["nome_alterador"] = ttk.Entry(self.campos_frame, width=30)
        self.action_fields["nome_alterador"].grid(row=linha + 1, column=1, sticky="w", pady=4)

        ttk.Label(self.campos_frame, text="Descrição da alteração:").grid(row=linha + 2, column=0, sticky="e", padx=(0, 6), pady=4)
        self.action_fields["descricao"] = ttk.Entry(self.campos_frame, width=30)
        self.action_fields["descricao"].grid(row=linha + 2, column=1, sticky="w", pady=4)

    def on_registro_selecionado(self, event):
        tabela = self.tabela_selecionada.get()
        item = self.tree.selection()
        if not item:
            return

        valores = self.tree.item(item[0], "values")
        self.original_values = list(valores)
        self.registro_id = None
        for idx, coluna in enumerate(self.colunas_info):
            nome = coluna["name"]
            valor = valores[idx] if idx < len(valores) else ""
            entry = self.entradas.get(nome)
            if entry:
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, valor)
                if coluna["pk"] and coluna["type"].upper().startswith("INT"):
                    entry.config(state="disabled")
                if coluna["pk"] and nome.lower() == "id":
                    self.registro_id = valor

        self.status_label.config(text=f"Selecionado registro {self.registro_id or 'sem ID'} da tabela '{tabela}'.")

    def limpar_formulario(self):
        self.registro_id = None
        self.original_values = []
        for nome, entrada in self.entradas.items():
            entrada.config(state="normal")
            entrada.delete(0, tk.END)
            coluna = next((c for c in self.colunas_info if c["name"] == nome), None)
            if coluna and coluna["pk"] and coluna["type"].upper().startswith("INT"):
                entrada.config(state="disabled")
        for campo in self.action_fields.values():
            campo.delete(0, tk.END)
        self.status_label.config(text="Formulário limpo. Preencha os dados para inserir ou editar um registro.")

    def abrir_dialogo_acao(self, acao):
        tabela = self.tabela_selecionada.get()
        if not tabela:
            messagebox.showwarning("Atenção", "Selecione uma tabela antes de prosseguir.")
            return

        if acao == "inseriu":
            self.realizar_insercao(tabela)
            return

        if acao == "excluiu":
            self.realizar_exclusao(tabela)
            return

        if acao == "editou":
            self.realizar_edicao(tabela)
            return

    def validar_campos_acao(self, acao, campos):
        nome_alterador = self.action_fields["nome_alterador"].get().strip()
        descricao = self.action_fields["descricao"].get().strip()
        if not nome_alterador:
            messagebox.showwarning("Atenção", "Preencha o nome de quem altera.")
            return None, None
        if not descricao:
            messagebox.showwarning("Atenção", "Preencha a descrição da alteração.")
            return None, None

        return nome_alterador, descricao

    def montar_descricao_padrao(self, acao, colunas):
        tabela = self.tabela_selecionada.get()
        if isinstance(colunas, list):
            return f"{tabela}/{','.join(colunas)}/{acao}"
        return f"{tabela}/{colunas}/{acao}"

    def realizar_insercao(self, tabela):
        valores = {}
        for coluna in self.colunas_info:
            nome = coluna["name"]
            entrada = self.entradas.get(nome)
            if entrada is None:
                continue
            valor = entrada.get().strip()
            if coluna["notnull"] and not valor and not (coluna["pk"] and coluna["type"].upper().startswith("INT")):
                messagebox.showwarning("Atenção", f"Preencha o campo {nome}.")
                return
            valores[nome] = valor

        nome_alterador = self.action_fields["nome_alterador"].get().strip()
        descricao = self.action_fields["descricao"].get().strip()
        if not nome_alterador:
            messagebox.showwarning("Atenção", "Preencha o nome de quem altera.")
            return
        if not descricao:
            descricao = self.montar_descricao_padrao("inseriu", [c["name"] for c in self.colunas_info])
            self.action_fields["descricao"].insert(0, descricao)

        colunas_insert = [nome for nome in valores.keys() if not (next(c for c in self.colunas_info if c["name"] == nome)["pk"] and next(c for c in self.colunas_info if c["name"] == nome)["type"].upper().startswith("INT") and valores[nome] == "")]
        placeholders = ", ".join("?" for _ in colunas_insert)
        sql = f"INSERT INTO {tabela} ({', '.join(colunas_insert)}) VALUES ({placeholders})"
        parametros = [valores[col] for col in colunas_insert]

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, parametros)
            conn.commit()
            registro_id = cursor.lastrowid
            inserir_log(tabela, registro_id, ",".join(colunas_insert), "inseriu", nome_alterador, descricao)
            messagebox.showinfo("Sucesso", "Registro inserido com sucesso.")
            self.carregar_registros_da_tabela()
        except sqlite3.IntegrityError as err:
            messagebox.showerror("Erro", f"Falha ao inserir: {err}")
        finally:
            conn.close()

    def realizar_edicao(self, tabela):
        if not self.registro_id:
            messagebox.showwarning("Atenção", "Selecione um registro para editar.")
            return

        valores = {}
        for idx, coluna in enumerate(self.colunas_info):
            nome = coluna["name"]
            entrada = self.entradas.get(nome)
            if entrada is None:
                continue
            valor = entrada.get().strip()
            valores[nome] = valor

        campos_alterados = []
        parametros = []
        for idx, coluna in enumerate(self.colunas_info):
            nome = coluna["name"]
            if coluna["pk"] and nome.lower() == "id":
                continue
            original = self.original_values[idx] if idx < len(self.original_values) else ""
            novo = valores[nome]
            if str(original) != str(novo):
                campos_alterados.append(nome)
                parametros.append(novo)

        if not campos_alterados:
            messagebox.showinfo("Informação", "Nenhuma alteração detectada.")
            return

        nome_alterador = self.action_fields["nome_alterador"].get().strip()
        descricao = self.action_fields["descricao"].get().strip()
        if not nome_alterador:
            messagebox.showwarning("Atenção", "Preencha o nome de quem altera.")
            return
        if not descricao:
            descricao = self.montar_descricao_padrao("editou", campos_alterados)
            self.action_fields["descricao"].insert(0, descricao)

        sets = ", ".join(f"{col}= ?" for col in campos_alterados)
        sql = f"UPDATE {tabela} SET {sets} WHERE id = ?"
        parametros.append(self.registro_id)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, parametros)
            conn.commit()
            inserir_log(tabela, self.registro_id, ",".join(campos_alterados), "editou", nome_alterador, descricao)
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso.")
            self.carregar_registros_da_tabela()
        except sqlite3.OperationalError as err:
            messagebox.showerror("Erro", f"Falha ao atualizar: {err}")
        finally:
            conn.close()

    def realizar_exclusao(self, tabela):
        if not self.registro_id:
            messagebox.showwarning("Atenção", "Selecione um registro para excluir.")
            return

        confirmado = messagebox.askyesno(
            "Confirmar exclusão",
            "Tem certeza que deseja excluir o registro selecionado?",
        )
        if not confirmado:
            return

        nome_alterador = self.action_fields["nome_alterador"].get().strip()
        descricao = self.action_fields["descricao"].get().strip()
        if not nome_alterador:
            messagebox.showwarning("Atenção", "Preencha o nome de quem altera.")
            return
        if not descricao:
            descricao = self.montar_descricao_padrao("excluiu", "registro")
            self.action_fields["descricao"].insert(0, descricao)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (self.registro_id,))
            conn.commit()
            inserir_log(tabela, self.registro_id, "registro", "excluiu", nome_alterador, descricao)
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso.")
            self.carregar_registros_da_tabela()
        except sqlite3.OperationalError as err:
            messagebox.showerror("Erro", f"Falha ao excluir: {err}")
        finally:
            conn.close()

    def ver_alteracoes(self):
        janela = tk.Toplevel(self)
        janela.title("Histórico de Alterações")
        janela.geometry("860x480")

        tree = ttk.Treeview(janela, columns=("data_hora", "tabela", "registro_id", "coluna", "acao", "nome_alterador", "descricao"), show="headings")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        colunas = ["data_hora", "tabela", "registro_id", "coluna", "acao", "nome_alterador", "descricao"]
        labels = ["Data/Hora", "Tabela", "Registro", "Coluna", "Ação", "Alterador", "Descrição"]
        for coluna, label in zip(colunas, labels):
            tree.heading(coluna, text=label)
            tree.column(coluna, width=120, anchor="w")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT data_hora, tabela, registro_id, coluna, acao, nome_alterador, descricao FROM alteracoes ORDER BY data_hora DESC")
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)
        conn.close()


if __name__ == "__main__":
    app = App()
    app.mainloop()
