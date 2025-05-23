import fitz  # PyMuPDF
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extrair_texto(caminho_pdf: str):
    """Extrai o texto de todas as páginas do PDF especificado e retorna uma lista de strings (uma por página)."""
    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"O arquivo PDF não foi encontrado: {caminho_pdf}")
        
    texto_paginas = []
    try:
        with fitz.open(caminho_pdf) as doc:
            if doc.page_count == 0:
                logger.warning(f"PDF sem páginas: {caminho_pdf}")
                return []
                
            for pagina in doc:
                try:
                    texto = pagina.get_text()  # extrai o texto bruto da página
                    # Normalização básica: remover espaços extras no início/fim
                    texto = texto.strip()
                    texto_paginas.append(texto)
                except Exception as e:
                    logger.error(f"Erro ao extrair texto da página {pagina.number}: {str(e)}")
                    texto_paginas.append(f"[ERRO DE EXTRAÇÃO NA PÁGINA {pagina.number+1}]")
    except Exception as e:
        logger.error(f"Erro ao processar o PDF {caminho_pdf}: {str(e)}")
        raise ValueError(f"Não foi possível processar o PDF. Erro: {str(e)}")
            
    return texto_paginas

def salvar_pdf_anon(texto_paginas_anonimizado: list, caminho_pdf_original: str):
    """Gera um PDF novo com o texto anonimizado. Retorna o caminho do arquivo PDF salvo."""
    if not texto_paginas_anonimizado:
        raise ValueError("Nenhum texto anonimizado fornecido para salvar no PDF.")
        
    nome_base, _ = os.path.splitext(caminho_pdf_original)
    caminho_saida = nome_base + "_anon.pdf"
    
    try:
        doc = fitz.open()  # cria um novo documento PDF vazio
        
        for i, texto in enumerate(texto_paginas_anonimizado):
            try:
                # Cria uma nova página e insere o texto anonimizado na posição (72,72) 
                # (1 polegada de margem nas bordas) com fonte padrão.
                pagina = doc.new_page()
                
                # Adiciona número da página e configurações melhores para texto
                pagina.insert_text(fitz.Point(72, 72), texto, fontsize=11)
                
                # Adiciona número da página no rodapé
                pagina.insert_text(
                    fitz.Point(72, pagina.rect.height - 72),
                    f"Página {i + 1} de {len(texto_paginas_anonimizado)} - Documento Anonimizado",
                    fontsize=8
                )
            except Exception as e:
                logger.error(f"Erro ao processar página {i+1}: {str(e)}")
                # Criar página com mensagem de erro
                pagina = doc.new_page()
                pagina.insert_text(fitz.Point(72, 72), f"[ERRO AO PROCESSAR PÁGINA {i+1}]")
        
        try:
            doc.save(caminho_saida)
            logger.info(f"PDF anonimizado salvo em: {caminho_saida}")
        except Exception as e:
            logger.error(f"Erro ao salvar o PDF: {str(e)}")
            # Tenta salvar em local alternativo se houver erro de permissão
            alternative_path = os.path.join(os.path.expanduser("~"), f"documento_anonimizado_{os.path.basename(caminho_saida)}")
            doc.save(alternative_path)
            logger.info(f"PDF salvo em local alternativo: {alternative_path}")
            return alternative_path
            
        return caminho_saida
    except Exception as e:
        logger.error(f"Erro ao criar PDF anonimizado: {str(e)}")
        raise ValueError(f"Não foi possível criar o PDF anonimizado. Erro: {str(e)}")
    finally:
        if 'doc' in locals():
            doc.close()