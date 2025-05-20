import transformers
import re

# Compila novamente os mesmos padrões de identificação para reutilizar aqui
PADRAO_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
PADRAO_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PADRAO_TEL = re.compile(r"\b(?:\+\d{1,3}\s?)?(?:\(?\d{2,3}\)?\s?)?\d{4,5}-?\d{4}\b")

# Carrega o modelo e tokenizer do DistilGPT-2
tokenizer = transformers.AutoTokenizer.from_pretrained("distilgpt2")
modelo = transformers.AutoModelForCausalLM.from_pretrained("distilgpt2")

def validar_anonimizacao(texto_anon: str, max_tokens_input: int = 1000, max_tokens_output: int = 50):
    """Usa o modelo DistilGPT-2 para validar se o texto anonimizado ainda contém dados pessoais.
       Retorna (texto_gerado, lista_indicadores_encontrados)."""
    # Tokeniza o texto e trunca se ultrapassar o limite de tokens
    inputs = tokenizer(texto_anon, return_tensors='pt', truncation=True, max_length=max_tokens_input)
    input_ids = inputs['input_ids']
    prompt_length = input_ids.shape[1]
    # Gera continuacão de texto (máx max_tokens_output tokens gerados)
    output_ids = modelo.generate(input_ids, max_new_tokens=max_tokens_output, do_sample=False)
    # A saída inclui o prompt + novos tokens; ignoramos os tokens iniciais do prompt
    generated_ids = output_ids[0][prompt_length:]
    texto_gerado = tokenizer.decode(generated_ids, skip_special_tokens=True)
    # Verifica padrões de dados pessoais no texto gerado
    indicadores = []
    if PADRAO_EMAIL.search(texto_gerado):
        indicadores.append("email")
    if PADRAO_CPF.search(texto_gerado):
        indicadores.append("CPF")
    if PADRAO_TEL.search(texto_gerado):
        indicadores.append("telefone")
    # (Opcional: poderíamos usar NER novamente aqui para detectar nomes próprios na saída)
    return texto_gerado, indicadores
