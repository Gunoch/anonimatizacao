```python
import fitz  # PyMuPDF
import os

def extrair_texto(caminho_pdf: str):
    """Extrai o texto de todas as páginas do PDF especificado e retorna uma lista de strings (uma por página)."""
    texto_paginas = []
    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto = pagina.get_text()  # extrai o texto bruto da página
            # Normalização básica: remover espaços extras no início/fim
            texto = texto.strip()
            texto_paginas.append(texto)
    return texto_paginas

def salvar_pdf_anon(texto_paginas_anonimizado: list, caminho_pdf_original: str):
    """Gera um PDF novo com o texto anonimizado. Retorna o caminho do arquivo PDF salvo."""
    nome_base, _ = os.path.splitext(caminho_pdf_original)
    caminho_saida = nome_base + "_anon.pdf"
    doc = fitz.open()  # cria um novo documento PDF vazio
    for texto in texto_paginas_anonimizado:
        # Cria uma nova página e insere o texto anonimizado na posição (72,72) 
        # (1 polegada de margem nas bordas) com fonte padrão.
        pagina = doc.new_page()
        pagina.insert_text(fitz.Point(72, 72), texto)
    doc.save(caminho_saida)
    return caminho_saida
```