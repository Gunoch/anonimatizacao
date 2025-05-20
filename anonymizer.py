```python
from faker import Faker

faker = Faker("pt_BR")

def anonimizar_texto(textos_paginas: list, itens_sensiveis: dict):
    """Substitui todos os itens sensíveis nos textos fornecidos por valores fictícios.
       Retorna (textos_anonimizados, mapeamento_original_para_falso)."""
    mapeamento = {}   # dict {original: falso}
    valores_usados = set()
    # Gera substitutos fictícios para cada dado sensível único
    for original, categoria in itens_sensiveis.items():
        if original in mapeamento:
            continue  # já gerado
        # Gera valor falso baseado na categoria
        if categoria == "PERSON":
            falso = faker.name()        # nome completo falso
        elif categoria == "ORG":
            falso = faker.company()     # nome de empresa falso
        elif categoria == "LOC":
            falso = faker.city()        # nome de cidade (ou local) falso
        elif categoria == "EMAIL":
            falso = faker.email()
        elif categoria == "PHONE":
            falso = faker.phone_number()
        elif categoria == "CPF":
            falso = faker.cpf()         # CPF formatado falso (com máscara nnn.nnn.nnn-nn)
        else:
            falso = faker.word()        # fallback: palavra aleatória
        # Garante que o valor falso seja único (evita colisão acidental)
        while falso in valores_usados:
            # Gera outro valor até ser único
            if categoria == "PERSON":
                falso = faker.name()
            elif categoria == "ORG":
                falso = faker.company()
            elif categoria == "LOC":
                falso = faker.city()
            elif categoria == "EMAIL":
                falso = faker.email()
            elif categoria == "PHONE":
                falso = faker.phone_number()
            elif categoria == "CPF":
                falso = faker.cpf()
            else:
                falso = faker.word()
        valores_usados.add(falso)
        mapeamento[original] = falso
    # Realiza as substituições em cada página
    textos_anonimizados = []
    # Para evitar substituições parciais indevidas, ordena chaves por comprimento decrescente
    chaves_sensiveis = sorted(mapeamento.keys(), key=len, reverse=True)
    for texto in textos_paginas:
        texto_anon = texto
        for original in chaves_sensiveis:
            falso = mapeamento[original]
            texto_anon = texto_anon.replace(original, falso)
        textos_anonimizados.append(texto_anon)
    return textos_anonimizados, mapeamento
```