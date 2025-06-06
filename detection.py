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
        self._load_custom_patterns()
    
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
                self.entity_ruler = self.nlp.add_pipe('entity_ruler', before='ner')
            else:
                self.entity_ruler = self.nlp.get_pipe('entity_ruler')

            self.entity_ruler.add_patterns(ENTITY_RULER_PATTERNS)

            logger.info("spaCy model loaded successfully with EntityRuler")

        except OSError:
            logger.error("spaCy model 'pt_core_news_sm' not found. Please download it by running:")
            logger.error("python -m spacy download pt_core_news_sm")
            self.nlp = None

    def _load_custom_patterns(self) -> None:
        """Load custom regex patterns from 'custom_patterns.json' if available."""
        import json
        import os

        patterns_file = 'custom_patterns.json'
        if not os.path.exists(patterns_file):
            return

        try:
            with open(patterns_file, 'r', encoding='utf-8') as f:
                custom_patterns = json.load(f)

            for name, pattern in custom_patterns.items():
                self.regex_patterns[name] = re.compile(pattern)
                logger.info(f"Loaded custom regex pattern: {name}")
        except Exception as e:
            logger.error(f"Failed to load custom patterns: {e}")

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
