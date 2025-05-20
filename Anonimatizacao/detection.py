'''Module for detecting sensitive data using spaCy and regex.'''
import re
import spacy

# Load the Portuguese spaCy model
# Make sure to download it first: python -m spacy download pt_core_news_sm
try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("spaCy model 'pt_core_news_sm' not found. Please download it by running:")
    print("python -m spacy download pt_core_news_sm")
    # Fallback or raise an error if the model is critical for the module's function
    nlp = None 

# Regular expressions for PII
CPF_REGEX = r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"
PHONE_REGEX = r"(\+?55\s?)?(\(?\d{2}\)?\s?)\d{4,5}-?\d{4}"
EMAIL_REGEX = r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b"

# Define PII types for clarity
PII_TYPES = {
    "CPF": "CPF",
    "TELEFONE": "TELEFONE",
    "EMAIL": "EMAIL",
    "NOME": "PER", # spaCy's PER (Person)
    "LOCAL": "LOC", # spaCy's LOC (Location)
    "ORGANIZACAO": "ORG", # spaCy's ORG (Organization)
    "MISC": "MISC" # spaCy's MISC (Miscellaneous)
}

def detect_sensitive_data(text: str) -> list[dict[str, str]]:
    """
    Detects sensitive data (PII) in a given text using spaCy NER and regular expressions.

    Args:
        text: The input text to analyze.

    Returns:
        A list of dictionaries, where each dictionary represents a detected sensitive item
        and contains 'text' (the detected string) and 'type' (the PII type).
        Returns an empty list if no sensitive data is found or if nlp model is not loaded.
    """
    if nlp is None:
        print("spaCy model not loaded. Cannot perform NER.")
        return []

    detected_items = []
    processed_texts = set() # To avoid duplicate entries of the exact same text span

    # 1. Named Entity Recognition (NER) with spaCy
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC", "ORG", "MISC"]:
            # Ensure we don't add empty or whitespace-only entities
            if ent.text.strip() and ent.text not in processed_texts:
                detected_items.append({"text": ent.text, "type": PII_TYPES.get(ent.label_, ent.label_)})
                processed_texts.add(ent.text)

    # 2. Regular Expressions for PII
    # CPF
    for match in re.finditer(CPF_REGEX, text):
        cpf = match.group(0)
        if cpf not in processed_texts:
            detected_items.append({"text": cpf, "type": PII_TYPES["CPF"]})
            processed_texts.add(cpf)
            
    # Telefones
    for match in re.finditer(PHONE_REGEX, text):
        phone = match.group(0)
        if phone not in processed_texts:
            detected_items.append({"text": phone, "type": PII_TYPES["TELEFONE"]})
            processed_texts.add(phone)

    # E-mails
    for match in re.finditer(EMAIL_REGEX, text):
        email = match.group(0)
        if email not in processed_texts:
            detected_items.append({"text": email, "type": PII_TYPES["EMAIL"]})
            processed_texts.add(email)
            
    # 3. Unification of Results (handled by processed_texts set for basic deduplication)
    # More sophisticated deduplication might be needed if spaCy and regex overlap
    # e.g. spaCy identifies "email@example.com" as MISC and regex identifies it as EMAIL.
    # For now, we accept both if their text representation is slightly different or if one is a substring of another.
    # A more robust approach would be to check for overlapping spans.

    # A simple way to further remove duplicates that might have different types but same text
    final_detected_items = []
    seen_texts_for_final_list = set()
    for item in detected_items:
        if item["text"] not in seen_texts_for_final_list:
            final_detected_items.append(item)
            seen_texts_for_final_list.add(item["text"])
            
    return final_detected_items

def encontrar_dados_sensiveis(textos_paginas: list):
    """Retorna um dicionário de dados sensíveis encontrados mapeando o texto original para sua categoria."""
    encontrados = {}  # mapeia string sensível -> categoria
    # Verifica cada página separadamente para considerar quebra de página
    for texto in textos_paginas:
        # 1. Named Entity Recognition (spaCy)
        doc = nlp(texto)
        for ent in doc.ents:
            label = ent.label_
            # Considera apenas entidades de interesse: pessoas, locais e organizações
            if label in ("PERSON", "PER"):
                encontrados[ent.text] = "PERSON"
            elif label in ("ORG",):
                encontrados[ent.text] = "ORG"
            elif label in ("GPE", "LOC"):
                encontrados[ent.text] = "LOC"
        # 2. Regex para CPF
        for match in re.finditer(CPF_REGEX, texto):
            cpf = match.group()
            encontrados[cpf] = "CPF"
        # 3. Regex para telefones
        for match in re.finditer(PHONE_REGEX, texto):
            tel = match.group()
            encontrados[tel] = "PHONE"
        # 4. Regex para e-mails
        for match in re.finditer(EMAIL_REGEX, texto):
            email = match.group()
            encontrados[email] = "EMAIL"
    # Resolver potenciais duplicatas entre CPF e PHONE (11 dígitos não formatados)
    duplicados = []
    for dado, categoria in encontrados.items():
        if categoria == "PHONE" and PADRAO_CPF.fullmatch(dado):
            # Se foi classificado como PHONE mas corresponde exatamente a um CPF (11 dígitos), marca para ajustar
            duplicados.append(dado)
    for dado in duplicados:
        encontrados[dado] = "CPF"
    return encontrados

# Example usage (optional, for testing the module directly)
if __name__ == '__main__':
    sample_text_pt = """
    A Sra. Joana Silva (CPF: 123.456.789-00) mora em São Paulo e trabalha na Empresa X.
    Seu telefone é (11) 98765-4321 e o e-mail para contato é joana.silva@emailaleatorio.com.
    Outro número é +55 (21) 12345-6789. O CNPJ da Empresa X é 12.345.678/0001-99 (não é PII pessoal).
    O Sr. João Doe, telefone 5511912345678, também foi mencionado.
    Reunião na Avenida Paulista, 1000, São Paulo, SP.
    Produto Y da Organização Z. Email: contato@organizacaoz.org.
    CPF inválido: 999.999.999-99.
    """

    print("Attempting to detect sensitive data in sample text...")
    if nlp: # Proceed only if spaCy model was loaded
        sensitive_data_found = detect_sensitive_data(sample_text_pt)
        if sensitive_data_found:
            print("\nDetected Sensitive Data:")
            for item in sensitive_data_found:
                print(f'- Text: "{item['text']}", Type: {item['type']}')
        else:
            print("No sensitive data detected in the sample text.")
    else:
        print("Skipping sensitive data detection example as spaCy model is not available.")

    # Test with a text that has only regex matches
    sample_text_regex_only = "Meu CPF é 000.111.222-33 e meu email é teste@exemplo.com."
    print("\nAttempting to detect sensitive data in regex-only sample text...")
    if nlp:
        sensitive_data_regex_only = detect_sensitive_data(sample_text_regex_only)
        if sensitive_data_regex_only:
            print("\nDetected Sensitive Data (Regex Only):")
            for item in sensitive_data_regex_only:
                print(f'- Text: "{item['text']}", Type: {item['type']}')
        else:
            print("No sensitive data detected in the regex-only sample text.")
            
    # Test with empty text
    print("\nAttempting to detect sensitive data in empty text...")
    if nlp:
        sensitive_data_empty = detect_sensitive_data("")
        if sensitive_data_empty:
            print("\nDetected Sensitive Data (Empty Text - should be none):")
            for item in sensitive_data_empty:
                print(f'- Text: "{item['text']}", Type: {item['type']}')
        else:
            print("No sensitive data detected in empty text, as expected.")
