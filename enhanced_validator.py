# -*- coding: utf-8 -*-
"""
Enhanced validation system for Portuguese PDF anonymization.
Uses multiple approaches for robust PII detection in anonymized text.
"""

import re
import logging
import torch
from typing import List, Tuple, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from config import VALIDATION_CONFIG, ERROR_MESSAGES, STOP_TERMS
import spacy

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedValidator:
    """
    Enhanced validator for Portuguese anonymized documents using multiple validation approaches.
    """
    
    def __init__(self):
        self.validation_patterns = self._compile_patterns()
        self.nlp_model = self._load_spacy_model()
        self.pii_classifier = self._load_pii_classifier()
        self.sentiment_analyzer = self._load_sentiment_analyzer()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection."""
        patterns = {}
        
        # Enhanced patterns for Portuguese documents
        enhanced_patterns = {
            **VALIDATION_CONFIG['patterns'],
            
            # Brazilian-specific patterns
            'titulo_eleitor': r'\\b\\d{4}\\s?\\d{4}\\s?\\d{4}\\b',
            'pis_pasep': r'\\b\\d{3}\\.?\\d{5}\\.?\\d{2}-?\\d\\b',
            'carteira_trabalho': r'\\b\\d{7}/?\\d{4}\\b',
              # Address patterns (more comprehensive)
            'endereco_completo': r'\\b(?:Rua|Av\\.?|Avenida|Alameda|Travessa|Praça|Rodovia)\\s+[A-Za-zÀ-ÿ0-9\\s]+,?\\s*\\d+[A-Za-z0-9\\s,.-]*\\b',
            'cep_formatted': r'\\b\\d{5}-\\d{3}\\b',
            'bairro_pattern': r'\\b(?:Bairro|B\\.)\\s+[A-Za-zÀ-ÿ\\s]+\\b',
              # Name patterns (more sophisticated)
            'nome_completo': r'\\b[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß][a-zàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]+(?:\\s+(?:da|de|do|das|dos|e)\\s+)?(?:[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß][a-zàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]+\\s*){1,3}\\b',
            'nome_proprio': r'\\b[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß][a-zàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]{2,}\\b',
            
            # Legal document patterns
            'processo_numero': r'\\b\\d{7}-?\\d{2}\\.?\\d{4}\\.?\\d\\.?\\d{2}\\.?\\d{4}\\b',
            'oab_numero': r'\\b(?:OAB[/-]?)?\\d{1,6}[/-]?[A-Z]{2}\\b',
            
            # Bank and financial
            'conta_bancaria': r'\\b\\d{4,5}-?\\d{1,2}\\b',
            'agencia_bancaria': r'\\b\\d{4}-?\\d\\b',
            
            # Vehicle and license
            'placa_veiculo': r'\\b[A-Z]{3}-?\\d{4}\\b|[A-Z]{3}\\d[A-Z]\\d{2}\\b',
            'cnh_numero': r'\\b\\d{11}\\b',
            
            # Potentially leaked data patterns
            'data_nascimento': r'\\b(?:\\d{1,2}[/.-]\\d{1,2}[/.-]\\d{4}|\\d{4}[/.-]\\d{1,2}[/.-]\\d{1,2})\\b',
            'suspicious_numbers': r'\\b\\d{8,15}\\b',  # Long number sequences
        }
        for pattern_name, pattern_value in enhanced_patterns.items():
            try:
                patterns[pattern_name] = re.compile(pattern_value, re.IGNORECASE)
                logger.debug(f"Compiled pattern '{pattern_name}'")
            except re.error as e:
                logger.error(f"Failed to compile pattern '{pattern_name}': {e}")
                
        return patterns
    
    def _load_spacy_model(self) -> Optional[object]:
        """Load spaCy model for NER."""
        try:
            nlp = spacy.load('pt_core_news_sm')
            logger.info("Loaded spaCy Portuguese model successfully")
            return nlp
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            return None
    
    def _load_pii_classifier(self) -> Optional[object]:
        """Load a multilingual model for PII classification."""
        try:
            # Use a simpler approach since BERT models need specific training for PII
            # We'll use this mainly for entity recognition rather than classification
            model_name = "neuralmind/bert-base-portuguese-cased"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Create a simple tokenizer-based approach for now
            # In a production environment, you'd want a model specifically trained for PII
            logger.info(f"Loaded tokenizer for Portuguese text analysis: {model_name}")
            return tokenizer
            
        except Exception as e:
            logger.warning(f"Failed to load PII classifier: {e}")
            return None
            
    def _load_sentiment_analyzer(self) -> Optional[object]:
        """Load sentiment analyzer to detect emotional content that might indicate PII."""
        try:
            # Use a simpler approach that doesn't require heavy model downloads
            # Focus on pattern-based detection for better performance
            logger.info("Using pattern-based sentiment analysis for PII detection")
            return "pattern_based"  # Simple flag to indicate this is available
            
        except Exception as e:
            logger.warning(f"Failed to load sentiment analyzer: {e}")
            return None

    def validate_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Validate text using regex patterns."""
        findings = []
        
        for pattern_name, pattern in self.validation_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                # Check if match is a stop term
                matched_text = match.group().lower()
                if matched_text not in STOP_TERMS and self._is_valid_match(matched_text, pattern_name):
                    findings.append({
                        'type': 'pattern',
                        'category': pattern_name,
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': self._calculate_pattern_confidence(match.group(), pattern_name),
                        'severity': self._get_severity(pattern_name)
                    })
        
        return findings
    
    def _is_valid_match(self, text: str, pattern_name: str) -> bool:
        """Check if a pattern match is valid (not a false positive)."""
        # Common false positives to filter out
        false_positives = {
            'nome_proprio': {'dr', 'dra', 'sr', 'sra', 'art', 'lei', 'inc', 'par'},
            'suspicious_numbers': {'2023', '2024', '2025', '2022', '2021', '2020'},
            'nome_completo': {'Código Civil', 'Código Penal', 'Lei Maria', 'Lei Seca'}
        }
        
        if pattern_name in false_positives:
            return text.lower() not in false_positives[pattern_name]
        
        # Additional validation for specific patterns
        if pattern_name == 'cpf_pattern':
            return self._validate_cpf_checksum(text)
        elif pattern_name == 'cnpj_pattern':
            return self._validate_cnpj_checksum(text)
        
        return True
    
    def _calculate_pattern_confidence(self, text: str, pattern_name: str) -> float:
        """Calculate confidence score for pattern matches."""
        base_confidence = 0.9  # High confidence for regex matches
        
        # Adjust based on pattern type
        if pattern_name in ['cpf_pattern', 'cnpj_pattern', 'email_pattern']:
            # These have strong structural validation
            base_confidence = 0.95
        elif pattern_name in ['nome_proprio', 'suspicious_numbers']:
            # These are more prone to false positives
            base_confidence = 0.6
        
        # Adjust based on text characteristics
        if len(text) < 3:
            base_confidence -= 0.2
        
        return max(0.1, min(1.0, base_confidence))
    
    def _validate_cpf_checksum(self, cpf: str) -> bool:
        """Validate CPF checksum to reduce false positives."""
        # Remove formatting
        cpf_digits = re.sub(r'[^\d]', '', cpf)
        
        if len(cpf_digits) != 11:
            return False
        
        # Check for obvious invalid patterns
        if cpf_digits == cpf_digits[0] * 11:  # All same digits
            return False
        
        # Basic checksum validation (simplified)
        try:
            # Convert to integers
            digits = [int(d) for d in cpf_digits]
            
            # Calculate first check digit
            sum1 = sum(digits[i] * (10 - i) for i in range(9))
            check1 = (sum1 * 10) % 11
            if check1 == 10:
                check1 = 0
            
            # Calculate second check digit
            sum2 = sum(digits[i] * (11 - i) for i in range(10))
            check2 = (sum2 * 10) % 11
            if check2 == 10:
                check2 = 0
            
            return digits[9] == check1 and digits[10] == check2
        except Exception:
            return False

    def _validate_cnpj_checksum(self, cnpj: str) -> bool:
        """Validate CNPJ checksum to reduce false positives."""
        # Remove formatting
        cnpj_digits = re.sub(r'[^\d]', '', cnpj)
        
        if len(cnpj_digits) != 14:
            return False
        
        # Check for obvious invalid patterns
        if cnpj_digits == cnpj_digits[0] * 14:
            return False
        
        # Basic structure validation
        try:
            digits = [int(d) for d in cnpj_digits]
            
            # Simplified validation - just check it's not all zeros or obviously fake
            return sum(digits) > 0 and not all(d == digits[0] for d in digits)
        except Exception:
            return False
    
    def validate_with_ner(self, text: str) -> List[Dict[str, Any]]:
        """Validate text using Named Entity Recognition."""
        findings = []
        
        if not self.nlp_model:
            return findings
        
        try:
            doc = self.nlp_model(text)
            
            for ent in doc.ents:
                # Filter out entities that are in stop terms
                entity_text_lower = ent.text.lower()
                if entity_text_lower not in STOP_TERMS:
                    # Focus on person, organization, and location entities
                    if ent.label_ in ['PER', 'ORG', 'LOC', 'MISC']:
                        # Calculate confidence based on entity length and context
                        confidence = self._calculate_ner_confidence(ent)
                        
                        findings.append({
                            'type': 'ner',
                            'category': ent.label_,
                            'text': ent.text,
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'confidence': confidence,
                            'severity': self._get_ner_severity(ent.label_)
                        })
                        
        except Exception as e:
            logger.error(f"Error in NER validation: {e}")
            
        return findings
    
    def _calculate_ner_confidence(self, ent) -> float:
        """Calculate confidence score for NER entities."""
        base_confidence = 0.8
        
        # Adjust confidence based on entity characteristics
        text_length = len(ent.text)
        
        # Longer entities are generally more reliable
        if text_length > 10:
            base_confidence += 0.1
        elif text_length < 3:
            base_confidence -= 0.2
        
        # Check if entity contains numbers (might be false positive)
        if any(char.isdigit() for char in ent.text):
            base_confidence -= 0.1
        
        # Check if entity is all uppercase (might be acronym)
        if ent.text.isupper() and text_length > 1:
            base_confidence -= 0.15
        
        return max(0.1, min(1.0, base_confidence))
    
    def validate_context_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Analyze text context for potential PII leakage."""
        findings = []
        
        # Look for suspicious patterns that might indicate PII
        suspicious_patterns = [
            (r'\b(?:nome|sobrenome|apelido)[:]\s*[A-Za-zÀ-ÿ\s]+', 'potential_name_disclosure'),
            (r'\b(?:telefone|celular|fone)[:]\s*[\d\s\(\)-]+', 'potential_phone_disclosure'),
            (r'\b(?:endereço|rua|avenida)[:]\s*[A-Za-zÀ-ÿ\d\s,.-]+', 'potential_address_disclosure'),
            (r'\b(?:nascido|nasceu|idade)[:]\s*[\d/.-]+', 'potential_birth_disclosure'),
            (r'\b(?:cpf|rg|documento)[:]\s*[\d\s.-]+', 'potential_document_disclosure'),
        ]
        
        for pattern, category in suspicious_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    'type': 'context',
                    'category': category,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.7,
                    'severity': 'high'
                })
        
        return findings
    
    def _get_severity(self, pattern_name: str) -> str:
        """Get severity level for a pattern type."""
        high_severity = ['cpf_pattern', 'rg_pattern', 'cnpj_pattern', 'email_pattern', 
                        'phone_pattern', 'nome_completo', 'endereco_completo']
        medium_severity = ['cep_pattern', 'nome_proprio', 'processo_numero']
        
        if pattern_name in high_severity:
            return 'high'
        elif pattern_name in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def _get_ner_severity(self, entity_label: str) -> str:
        """Get severity level for NER entity types."""
        severity_map = {
            'PER': 'high',    # Person
            'ORG': 'medium',  # Organization
            'LOC': 'medium',  # Location
            'MISC': 'low'     # Miscellaneous
        }
        return severity_map.get(entity_label, 'low')
    
    def comprehensive_validation(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive validation using all available methods."""
        logger.info("Starting comprehensive validation")
        
        # Collect findings from all validation methods
        pattern_findings = self.validate_with_patterns(text)
        ner_findings = self.validate_with_ner(text)
        context_findings = self.validate_context_analysis(text)
        
        # Combine all findings
        all_findings = pattern_findings + ner_findings + context_findings
        
        # Remove duplicates and overlapping findings
        unique_findings = self._deduplicate_findings(all_findings)
        
        # Calculate statistics
        stats = self._calculate_statistics(unique_findings, text)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(unique_findings, stats)
        
        result = {
            'total_findings': len(unique_findings),
            'findings': unique_findings,
            'statistics': stats,
            'recommendations': recommendations,
            'validation_complete': True,
            'risk_level': self._assess_risk_level(unique_findings)
        }
        
        logger.info(f"Validation complete: {len(unique_findings)} findings, "
                   f"risk level: {result['risk_level']}")
        
        return result
    
    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and overlapping findings."""
        if not findings:
            return []
        
        # Sort by start position
        findings.sort(key=lambda x: x['start'])
        
        deduplicated = []
        for finding in findings:
            # Check if this finding overlaps with any existing finding
            overlap = False
            for existing in deduplicated:
                if (finding['start'] < existing['end'] and 
                    finding['end'] > existing['start']):
                    # If overlap, keep the one with higher confidence
                    if finding['confidence'] > existing['confidence']:
                        deduplicated.remove(existing)
                        break
                    else:
                        overlap = True
                        break
            
            if not overlap:
                deduplicated.append(finding)
        
        return deduplicated
    
    def _calculate_statistics(self, findings: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Calculate validation statistics."""
        if not findings:
            return {
                'high_severity_count': 0,
                'medium_severity_count': 0,
                'low_severity_count': 0,
                'coverage_percentage': 0.0,
                'confidence_average': 0.0
            }
        
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        total_confidence = 0
        
        for finding in findings:
            severity_counts[finding['severity']] += 1
            total_confidence += finding['confidence']
        
        # Calculate text coverage (percentage of text that contains findings)
        total_chars = len(text)
        covered_chars = sum(finding['end'] - finding['start'] for finding in findings)
        coverage_percentage = (covered_chars / total_chars * 100) if total_chars > 0 else 0
        
        return {
            'high_severity_count': severity_counts['high'],
            'medium_severity_count': severity_counts['medium'],
            'low_severity_count': severity_counts['low'],
            'coverage_percentage': round(coverage_percentage, 2),
            'confidence_average': round(total_confidence / len(findings), 2)
        }
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], 
                                stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if stats['high_severity_count'] > 0:
            recommendations.append(
                f"⚠️ {stats['high_severity_count']} high-severity PII items detected. "
                "Review anonymization settings and re-process the document."
            )
        
        if stats['medium_severity_count'] > 3:
            recommendations.append(
                f"📋 {stats['medium_severity_count']} medium-severity items found. "
                "Consider reviewing and improving the stop-terms list."
            )
        
        if stats['coverage_percentage'] > 10:
            recommendations.append(
                f"📊 {stats['coverage_percentage']}% of text contains potential PII. "
                "This might indicate over-detection. Review patterns and stop-terms."
            )
        
        if stats['confidence_average'] < 0.7:
            recommendations.append(
                f"🎯 Average confidence is {stats['confidence_average']}. "
                "Low confidence detections might include false positives."
            )
        
        if not findings:
            recommendations.append(
                "✅ No PII detected in anonymized text. Document appears properly anonymized."
            )
        
        return recommendations
    
    def _assess_risk_level(self, findings: List[Dict[str, Any]]) -> str:
        """Assess overall risk level based on findings."""
        if not findings:
            return 'low'
        
        high_severity_count = sum(1 for f in findings if f['severity'] == 'high')
        medium_severity_count = sum(1 for f in findings if f['severity'] == 'medium')
        
        if high_severity_count > 0:
            return 'high'
        elif medium_severity_count > 2:
            return 'medium'
        else:
            return 'low'


# Legacy compatibility functions
def validar_anonimizacao(texto_anon: str, 
                        max_tokens_input: int = None, 
                        max_tokens_output: int = None) -> Tuple[str, List[str]]:
    """
    Legacy validation function for backward compatibility.
    Uses the enhanced validator but returns results in the old format.
    """
    try:
        validator = EnhancedValidator()
        result = validator.comprehensive_validation(texto_anon)
        
        # Convert to legacy format
        problematic_patterns = [
            f"{finding['category']}: {finding['text']}" 
            for finding in result['findings'] 
            if finding['severity'] == 'high'
        ]
        
        # Generate a summary text
        summary = f"Validation complete. Risk level: {result['risk_level']}. "
        summary += f"Found {result['total_findings']} potential issues."
        
        return summary, problematic_patterns
        
    except Exception as e:
        logger.error(f"Error in legacy validation: {e}")
        return f"Validation error: {e}", []


def validate_anonymization_quality(original_texts: List[str], 
                                 anonymized_texts: List[str], 
                                 mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Enhanced validation function that replaces the old one.
    """
    try:
        validator = EnhancedValidator()
        
        # Combine all anonymized texts for analysis
        combined_text = "\n".join(anonymized_texts)
        
        # Run comprehensive validation
        validation_result = validator.comprehensive_validation(combined_text)
        
        # Add mapping integrity check
        mapping_issues = []
        for original, replacement in mapping.items():
            if original.lower() in combined_text.lower():
                mapping_issues.append(f"Original value '{original}' still present")
        
        # Enhanced result format
        enhanced_result = {
            'patterns_detected': [
                {'pattern': f['category'], 'match': f['text']} 
                for f in validation_result['findings']
            ],
            'integrity_issues': mapping_issues,
            'statistics': {
                'total_substitutions': len(mapping),
                'text_length_change': len(combined_text) - len("\n".join(original_texts)),
                'coverage_percentage': validation_result['statistics']['coverage_percentage'],
                'high_severity_findings': validation_result['statistics']['high_severity_count'],
                'medium_severity_findings': validation_result['statistics']['medium_severity_count'],
                'confidence_average': validation_result['statistics']['confidence_average']
            },
            'recommendations': validation_result['recommendations'],
            'risk_level': validation_result['risk_level'],
            'validation_complete': validation_result['validation_complete']
        }
        
        logger.info(f"Quality validation complete. Risk level: {enhanced_result['risk_level']}")
