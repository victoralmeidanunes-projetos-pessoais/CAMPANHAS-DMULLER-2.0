from db_config import (
    criar_tabela,
    criar_tabela_historico,
    criar_usuario
)

criar_tabela()
criar_tabela_historico()

criar_usuario(
    "COMERCIAL",
    "DM.26",
    "ADMINISTRADOR"
)

print("Banco configurado corretamente.")