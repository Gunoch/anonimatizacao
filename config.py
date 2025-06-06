# -*- coding: utf-8 -*-
"""
Configurações para o sistema de anonimização de PDFs.
Este arquivo contém as configurações centralizadas incluindo:
- Stop-terms/whitelist para evitar over-anonymization
- Padrões regex melhorados
- Configurações de substituição
"""

# Whitelist/Stop-terms - termos que NUNCA devem ser anonimizados
STOP_TERMS = {
    # Termos jurídicos/legais comuns
    "delegacia", "delegado", "delegada", "juiz", "juíza", "promotor", "promotora",
    "advogado", "advogada", "defensor", "defensora", "escrivão", "escrivã",
    "testemunha", "réu", "ré", "vítima", "autor", "autora", "querelante",
    "investigado", "investigada", "denunciado", "denunciada", "acusado", "acusada",
    
    # Tempos e datas
    "horário", "hora", "data", "dia", "semana", "mês", "ano", "manhã", "tarde", "noite",
    "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    
    # Preposições, artigos e conectivos
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "para", "por", "com", "sem", "sob", "sobre", "entre", "contra", "durante",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "e", "ou", "mas", "porque", "quando", "onde", "como", "que", "se",
    
    # Termos processuais
    "processo", "inquérito", "ação", "procedimento", "audiência", "sessão",
    "depoimento", "oitiva", "interrogatório", "acareação", "reconhecimento",
    "perícia", "laudo", "exame", "auto", "termo", "ata", "certidão",
    
    # Documentos e identificação
    "documento", "identidade", "carteira", "passaporte", "título", "registro",
    "certidão", "comprovante", "declaração", "atestado", "relatório",
    
    # Locais institucionais genéricos
    "tribunal", "fórum", "vara", "comarca", "cartório", "tabelião", "ofício",
    "ministério", "secretaria", "departamento", "seção", "divisão",
    
    # Outros termos funcionais
    "presente", "ausente", "comparecer", "intimar", "notificar", "citar",
    "determinar", "ordenar", "deferir", "indeferir", "arquivar", "protocolar",
    
    # Termos técnicos
    "artigo", "parágrafo", "inciso", "alínea", "código", "lei", "decreto",
    "resolução", "portaria", "instrução", "normativa", "regulamento",
    
    # Direitos e garantias
    "direito", "garantia", "liberdade", "prisão", "fiança", "habeas", "corpus",
    "mandado", "ordem", "decisão", "sentença", "acórdão", "recurso",
    
    # Estados e condições
    "presente", "ausente", "informado", "comunicado", "cientificado",
    "intimado", "citado", "convocado", "arrolado", "qualificado"
}

# Converter para minúsculas para comparação case-insensitive
STOP_TERMS = {term.lower() for term in STOP_TERMS}

# Padrões regex melhorados com delimitadores de palavra
REGEX_PATTERNS = {
    'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    'phone': r'\b(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4,5}-?\d{4}\b',
    'email': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    'cep': r'\b\d{5}-?\d{3}\b',
    'rg': r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b',
    'cnpj': r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'
}

# Configurações de substituição
SUBSTITUTION_CONFIG = {
    'use_placeholders': True,  # Se True, usa placeholders; se False, usa Faker
    'placeholder_format': '[{entity_type}_{counter}]',  # Formato dos placeholders
    'preserve_structure': True,  # Preservar estrutura do documento
    'case_sensitive': False,   # Comparação case-sensitive para stop-terms
}

# Configurações do spaCy
SPACY_CONFIG = {
    'model': 'pt_core_news_sm',
    'disable_pipes': ['tagger', 'parser'],  # Desabilitar pipes desnecessários
    'batch_size': 1000,
    'n_process': 1
}

# Tipos de entidades para detectar
ENTITY_TYPES = {
    'PER': 'PESSOA',      # Pessoa
    'ORG': 'ORGANIZACAO', # Organização
    'LOC': 'LOCAL',       # Local
    'CPF': 'CPF',         # CPF
    'TELEFONE': 'TELEFONE', # Telefone
    'EMAIL': 'EMAIL',     # Email
    'CEP': 'CEP',         # CEP
    'RG': 'RG',           # RG
    'CNPJ': 'CNPJ'        # CNPJ
}

# Padrões para EntityRuler
ENTITY_RULER_PATTERNS = [
    # Padrões para CPF
    {"label": "CPF", "pattern": [{"TEXT": {"REGEX": r"\d{3}"}, "OP": "?"}, 
                                {"TEXT": ".", "OP": "?"}, 
                                {"TEXT": {"REGEX": r"\d{3}"}, "OP": "?"}, 
                                {"TEXT": ".", "OP": "?"}, 
                                {"TEXT": {"REGEX": r"\d{3}"}, "OP": "?"}, 
                                {"TEXT": "-", "OP": "?"}, 
                                {"TEXT": {"REGEX": r"\d{2}"}}]},
    
    # Padrões para telefone
    {"label": "TELEFONE", "pattern": [{"TEXT": {"REGEX": r"\(?\d{2}\)?"}, "OP": "?"}, 
                                     {"TEXT": {"REGEX": r"9?\d{4,5}"}, "OP": "?"}, 
                                     {"TEXT": "-", "OP": "?"}, 
                                     {"TEXT": {"REGEX": r"\d{4}"}}]},
    
    # Padrões para CEP
    {"label": "CEP", "pattern": [{"TEXT": {"REGEX": r"\d{5}"}}, 
                                {"TEXT": "-", "OP": "?"}, 
                                {"TEXT": {"REGEX": r"\d{3}"}}]},
    
    # Padrões para RG
    {"label": "RG", "pattern": [{"TEXT": {"REGEX": r"\d{1,2}"}}, 
                               {"TEXT": ".", "OP": "?"}, 
                               {"TEXT": {"REGEX": r"\d{3}"}}, 
                               {"TEXT": ".", "OP": "?"}, 
                               {"TEXT": {"REGEX": r"\d{3}"}}, 
                               {"TEXT": "-", "OP": "?"}, 
                               {"TEXT": {"REGEX": r"[0-9Xx]"}}]},
]

# Configurações de validação
VALIDATION_CONFIG = {
    'check_stop_terms': True,           # Verificar se stop-terms foram alterados
    'check_token_boundaries': True,     # Verificar problemas de tokenização
    'check_document_integrity': True,   # Verificar integridade do documento
    'min_confidence_threshold': 0.5,   # Limiar mínimo de confiança para detecção
    
    # Configurações do modelo de validação
    'model_name': 'microsoft/DialoGPT-medium',  # Modelo para validação
    'max_tokens_input': 1000,          # Máximo de tokens de entrada
    'max_tokens_output': 50,            # Máximo de tokens de saída
    'do_sample': False,                 # Usar amostragem durante geração
    'temperature': 1.0,                 # Temperatura para geração
    
    # Parâmetros do tokenizer
    'tokenizer_params': {
        'use_fast': True,
        'add_prefix_space': False
    },
    
    # Parâmetros do modelo
    'model_params': {
        'torch_dtype': 'auto',
        'device_map': 'auto'
    },
    
    # Padrões regex para validar se ainda existem dados sensíveis
    'patterns': {
        'cpf_pattern': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        'phone_pattern': r'\b(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4,5}-?\d{4}\b',
        'email_pattern': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        'cep_pattern': r'\b\d{5}-?\d{3}\b',
        'rg_pattern': r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b',
        'cnpj_pattern': r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
        'name_pattern': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Padrão básico de nomes
        'address_pattern': r'\b(?:Rua|Av|Avenida|Alameda|Travessa)\s+[A-Z][^,\n]+\b'
    }
}

# Configurações do validador aprimorado
ENHANCED_VALIDATION_CONFIG = {
    'use_enhanced_validator': True,      # Usar o validador aprimorado
    'portuguese_model': 'neuralmind/bert-base-portuguese-cased',  # Modelo em português
    'confidence_threshold': 0.7,        # Limiar de confiança mínimo
    'enable_ner_validation': True,      # Habilitar validação por NER
    'enable_context_analysis': True,    # Habilitar análise contextual
    'enable_pattern_validation': True,  # Habilitar validação por padrões
    'max_findings_display': 50,         # Máximo de achados para exibir
    'severity_weights': {               # Pesos para cálculo de risco
        'high': 3,
        'medium': 2,
        'low': 1
    },
    'overlap_threshold': 0.8,           # Limiar para considerar sobreposição
    'batch_size': 16,                   # Tamanho do batch para processamento
}

# Mensagens de erro e avisos
ERROR_MESSAGES = {
    'stop_term_modified': "Aviso: Termo funcional '{}' foi modificado no documento.",
    'token_boundary_error': "Erro: Problema de tokenização detectado em '{}'.",
    'low_confidence': "Aviso: Entidade '{}' detectada com baixa confiança ({:.2f}).",
    'document_integrity': "Erro: Integridade do documento comprometida após anonimização.",
    'validation_error': "Erro durante validação da anonimização",
    'model_load_error': "Erro ao carregar modelo de validação",
    'pattern_compilation_error': "Erro ao compilar padrão regex"
}

# Configurações de log
LOG_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'anonymization.log',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
