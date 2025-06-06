'''Module for detecting sensitive data using spaCy and regex with improved accuracy.'''
import re
import spacy
import logging
from typing import List, Dict, Set, Any
from spacy.pipeline import EntityRuler

# Import configurations
from config import (
    STOP_TERMS, REGEX_PATTERNS, SPACY_CONFIG, ENTITY_TYPES, 
    ENTITY_RULER_PATTERNS, VALIDATION_CONFIG, ERROR_MESSAGES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedPIIDetector:
    """Improved PII detector with stop-terms filtering and enhanced patterns."""
    
    def __init__(self):
        self.nlp = None
        self.entity_ruler = None
        self.stop_terms = STOP_TERMS
        self.regex_patterns = {name: re.compile(pattern) for name, pattern in REGEX_PATTERNS.items()}
        self.entity_counters = {entity_type: 0 for entity_type in ENTITY_TYPES.values()}
        self._load_model()
    
    def _load_model(self):
        """Load and configure the spaCy model with EntityRuler."""
        try:
            # Load spaCy model
            self.nlp = spacy.load(SPACY_CONFIG['model'])
            
            # Disable unnecessary pipes for better performance
            disabled_pipes = SPACY_CONFIG.get('disable_pipes', [])
            for pipe_name in disabled_pipes:
                if pipe_name in self.nlp.pipe_names:
                    self.nlp.disable_pipes(pipe_name)
            
            # Add EntityRuler before the NER component
            if 'entity_ruler' not in self.nlp.pipe_names:
                self.entity_ruler = EntityRuler(self.nlp, patterns=ENTITY_RULER_PATTERNS)
                self.nlp.add_pipe(self.entity_ruler, before='ner')
            
            logger.info("spaCy model loaded successfully with EntityRuler")
            
        except OSError:
            logger.error("spaCy model 'pt_core_news_sm' not found. Please download it by running:")
            logger.error("python -m spacy download pt_core_news_sm")
            self.nlp = None

    def _is_stop_term(self, text: str) -> bool:
        """Check if a term is in the stop-terms list."""
        return text.lower().strip() in self.stop_terms
    
    def _validate_entity(self, text: str, entity_type: str, confidence: float = 1.0) -> bool:
        """Validate if an entity should be anonymized."""
        # Check if it's a stop term
        if self._is_stop_term(text):
            logger.warning(ERROR_MESSAGES['stop_term_modified'].format(text))
            return False
        
        # Check confidence threshold
        if confidence < VALIDATION_CONFIG.get('min_confidence_threshold', 0.5):
            logger.warning(ERROR_MESSAGES['low_confidence'].format(text, confidence))
            return False
        
        # Additional validations can be added here
        return True
    
    def _extract_entities_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy NER with improved validation."""
        if not self.nlp:
            return []
        
        entities = []
        doc = self.nlp(text)
        
        for ent in doc.ents:
            # Map spaCy labels to our entity types
            entity_type = None
            if ent.label_ in ["PER", "PERSON"]:
                entity_type = "PESSOA"
            elif ent.label_ == "ORG":
                entity_type = "ORGANIZACAO"
            elif ent.label_ in ["LOC", "GPE"]:
                entity_type = "LOCAL"
            elif ent.label_ in ENTITY_TYPES.keys():
                entity_type = ENTITY_TYPES[ent.label_]
            
            if entity_type and ent.text.strip():
                # Validate entity before adding
                if self._validate_entity(ent.text, entity_type, 
                                       getattr(ent, 'confidence', 1.0)):
                    entities.append({
                        'text': ent.text,
                        'type': entity_type,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': getattr(ent, 'confidence', 1.0)
                    })
        
        return entities
    
    def _extract_entities_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using improved regex patterns."""
        entities = []
        
        for pattern_name, pattern in self.regex_patterns.items():
            entity_type = pattern_name.upper()
            
            for match in pattern.finditer(text):
                matched_text = match.group(0)
                
                # Validate entity before adding
                if self._validate_entity(matched_text, entity_type):
                    entities.append({
                        'text': matched_text,
                        'type': entity_type,
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 1.0  # Regex matches have high confidence
                    })
        
        return entities
    
    def _remove_overlaps(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping entities, preferring higher confidence and longer spans."""
        if not entities:
            return entities
        
        # Sort by start position, then by confidence (descending), then by length (descending)
        entities.sort(key=lambda x: (x['start'], -x['confidence'], -(x['end'] - x['start'])))
        
        filtered_entities = []
        last_end = -1
        
        for entity in entities:
            # If this entity doesn't overlap with the previous one, add it
            if entity['start'] >= last_end:
                filtered_entities.append(entity)
                last_end = entity['end']
        
        return filtered_entities
    
    def detect_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sensitive data with improved accuracy and validation.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected entities with metadata
        """
        if not text or not text.strip():
            return []
        
        all_entities = []
        
        # Extract entities using spaCy
        spacy_entities = self._extract_entities_with_spacy(text)
        all_entities.extend(spacy_entities)
        
        # Extract entities using regex
        regex_entities = self._extract_entities_with_regex(text)
        all_entities.extend(regex_entities)
        
        # Remove overlapping entities
        filtered_entities = self._remove_overlaps(all_entities)
        
        logger.info(f"Detected {len(filtered_entities)} entities after filtering")
        
        return filtered_entities

# Global detector instance
detector = ImprovedPIIDetector()

# Legacy functions for backward compatibility
def detect_sensitive_data(text: str) -> List[Dict[str, str]]:
    """Legacy function for backward compatibility."""
    entities = detector.detect_sensitive_data(text)
    # Convert to legacy format
    return [{'text': ent['text'], 'type': ent['type']} for ent in entities]

# Keep old regex patterns for compatibility
CPF_REGEX = REGEX_PATTERNS['cpf']
PHONE_REGEX = REGEX_PATTERNS['phone'] 
EMAIL_REGEX = REGEX_PATTERNS['email']
PADRAO_CPF = re.compile(CPF_REGEX)

# Keep old PII_TYPES for compatibility
PII_TYPES = {
    "CPF": "CPF",
    "TELEFONE": "TELEFONE", 
    "EMAIL": "EMAIL",
    "NOME": "PER",
    "LOCAL": "LOC",
    "ORGANIZACAO": "ORG",
    "MISC": "MISC"
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

def encontrar_dados_sensiveis(textos_paginas: List[str]) -> Dict[str, str]:
    """
    Legacy function for backward compatibility.
    Returns a dictionary mapping sensitive text to its category.
    """
    encontrados = {}
    
    for texto in textos_paginas:
        entities = detector.detect_sensitive_data(texto)
        for entity in entities:
            # Map new types to legacy types
            legacy_type = entity['type']
            if legacy_type == "PESSOA":
                legacy_type = "PERSON"
            elif legacy_type == "ORGANIZACAO":
                legacy_type = "ORG"
            elif legacy_type == "LOCAL":
                legacy_type = "LOC"
            elif legacy_type == "TELEFONE":
                legacy_type = "PHONE"
            
            encontrados[entity['text']] = legacy_type
    
    return encontrados

# Example usage and testing
if __name__ == '__main__':
    sample_text_pt = """
    A Sra. Joana Silva (CPF: 123.456.789-00) mora em São Paulo e trabalha na Empresa X.
    Seu telefone é (11) 98765-4321 e o e-mail para contato é joana.silva@emailaleatorio.com.
    Outro número é +55 (21) 12345-6789. O CNPJ da Empresa X é 12.345.678/0001-99.
    O Sr. João Doe, telefone 5511912345678, também foi mencionado.
    Reunião na Avenida Paulista, 1000, São Paulo, SP.
    Produto Y da Organização Z. Email: contato@organizacaoz.org.
    CPF inválido: 999.999.999-99.
    O Horário da audiência foi às 14h30. A Delegacia fica na rua principal.
    """

    print("Testing improved PII detection...")
    if detector.nlp:
        sensitive_data_found = detector.detect_sensitive_data(sample_text_pt)
        if sensitive_data_found:
            print("\nDetected Sensitive Data:")
            for item in sensitive_data_found:
                print(f"- Text: \"{item['text']}\", Type: {item['type']}, "
                      f"Confidence: {item['confidence']:.2f}")
        else:
            print("No sensitive data detected in the sample text.")
    else:
        print("Skipping test as spaCy model is not available.")

    # Test stop-terms filtering
    stop_terms_text = "O Delegado João Silva informou que o Horário da audiência é às 14h."
    print("\nTesting stop-terms filtering...")
    if detector.nlp:
        stop_terms_result = detector.detect_sensitive_data(stop_terms_text)
        print(f"Entities found (should exclude 'Delegado' and 'Horário'): {len(stop_terms_result)}")
        for item in stop_terms_result:
            print(f"- Text: \"{item['text']}\", Type: {item['type']}")
    else:
        print("Skipping stop-terms test as spaCy model is not available.")
