"""
Igbo Language Expert - Specialized expert for Igbo language and culture.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class IgboProverb:
    """Igbo proverb with translation and meaning."""
    igbo: str
    english: str
    meaning: str
    context: str = ""
    category: str = "wisdom"


@dataclass
class IgboWord:
    """Igbo word with definitions and usage."""
    word: str
    pronunciation: str
    part_of_speech: str
    definitions: List[str]
    examples: List[Tuple[str, str]]  # (igbo, english)
    dialects: Dict[str, str] = field(default_factory=dict)
    related_words: List[str] = field(default_factory=list)


class IgboKnowledgeBase:
    """
    Comprehensive knowledge base for Igbo language and culture.
    
    Includes:
    - Vocabulary with definitions
    - Proverbs (ilu) with translations
    - Cultural concepts (omenala)
    - Dialect variations
    - Common phrases
    """
    
    # Common Igbo proverbs
    PROVERBS = [
        IgboProverb(
            igbo="Onye ndi iro ji agha ala, onye nwe ya anwughi n'isi",
            english="He who fights for another man's land, dies in the forefront",
            meaning="Don't fight other people's battles at your own expense",
            context="War and loyalty",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Egbe bere ugo bere",
            english="Let the kite perch and let the eagle perch",
            meaning="Live and let live; tolerance and peaceful coexistence",
            context="Peace and tolerance",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Ife anyi jiri mara mmadu, ka ife anyi jiri mara chi anyi",
            english="How we know a person is more than how we know our god",
            meaning="Human relationships are more tangible than divine ones",
            context="Human relations",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Aka aja aja na-ewute ọnụ nnyu mmiri",
            english="A sandy hand brings a mouth that tastes water",
            meaning="Hard work brings satisfaction",
            context="Work ethic",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Onye isi wee hụ ụzọ, ya ga-aga",
            english="When the head sees a path, it will take it",
            meaning="Leaders should take initiative",
            context="Leadership",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Ọ bụ otu aka ji nwa mmiri, ka ọ bụ otu aka na-edu ya",
            english="It's the same hand that holds the water pot that guides it",
            meaning="The same person who creates a problem should solve it",
            context="Responsibility",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Uche bu ihe nwere ndu",
            english="Thought is what has life",
            meaning="Ideas are alive; thinking is essential",
            context="Intellect",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Mmadu abughi Chi ya",
            english="A person is not their own god",
            meaning="Humans are not omnipotent; humility is necessary",
            context="Humility",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Ihe dị mma dị oke",
            english="Good things are scarce",
            meaning="Quality is rare and valuable",
            context="Value",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Onye riri ọjọ ga-atụkwa ọjọ",
            english="He who eats poisonous yam will vomit yam",
            meaning="Evil deeds have consequences",
            context="Consequences",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Nwa mmiriụ ma mmiriụ",
            english="The water child knows the water spirit",
            meaning="Children inherit traits from their environment",
            context="Nature vs nurture",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Ọkụkọ na-eso ịnyinya anaghị eso ya n'oge",
            english="The chicken that follows the horse does not follow it in speed",
            meaning="Know your limitations",
            context="Self-awareness",
            category="wisdom"
        ),
        IgboProverb(
            igbo="A naghị agwa mmadụ ihe ọ ga-eme, ka ọ gaa n'ọma",
            english="One doesn't tell a person what to do to become good",
            meaning="Goodness comes from within",
            context="Character",
            category="philosophy"
        ),
        IgboProverb(
            igbo="Echi dị ime, ụtụtụ dị n'aka",
            english="Tomorrow is pregnant, the morning is in hand",
            meaning="Plan for the future while acting in the present",
            context="Planning",
            category="wisdom"
        ),
        IgboProverb(
            igbo="Oge ndi ozo bụ oge ndi nwe ya",
            english="Other people's time is their owners' time",
            meaning="Respect others' time",
            context="Respect",
            category="wisdom"
        )
    ]
    
    # Cultural concepts
    CULTURAL_CONCEPTS = {
        "chi": {
            "definition": "Personal spiritual guide or guardian angel; one's personal god",
            "significance": "Central to Igbo spirituality; each person has their own chi that influences their destiny",
            "usage": "Chi m, gị nwe onwe gị (My chi, you are your own master)"
        },
        "omenala": {
            "definition": "Tradition, custom, culture, way of life",
            "significance": "The totality of Igbo cultural practices and beliefs",
            "usage": "Omenala anyị siri ike (Our traditions are strong)"
        },
        "ndichie": {
            "definition": "Ancestors, elders who have passed on",
            "significance": "Ancestors are venerated and consulted in Igbo spirituality",
            "usage": "Ndichie anyị gọzie anyị (May our ancestors bless us)"
        },
        "alu": {
            "definition": "Taboo, abomination, forbidden act",
            "significance": "Acts that violate the natural and spiritual order",
            "usage": "Ọ bụ alu ime ihe ahụ (It is an abomination to do that)"
        },
        "ofu": {
            "definition": "Unity, oneness",
            "significance": "The Igbo value of unity and collective action",
            "usage": "Ọfụ bụ ike (Unity is strength)"
        },
        "umunna": {
            "definition": "Kinship group, extended family",
            "significance": "The fundamental social unit in Igbo society",
            "usage": "Umunna m (My kinsmen)"
        },
        "nkali": {
            "definition": "Power, dominance, force",
            "significance": "The concept of power and its exercise",
            "usage": "Nkali anaghị eme ka eziokwu pụta (Power doesn't bring out truth)"
        },
        "igwebuike": {
            "definition": "There is strength in unity/numbers",
            "significance": "Philosophy of collective action and solidarity",
            "usage": "Igwebuike bụ ike anyị (Unity is our strength)"
        }
    }
    
    # Common vocabulary
    VOCABULARY = {
        "ndewo": IgboWord(
            word="ndewo",
            pronunciation="n-de-wo",
            part_of_speech="interjection",
            definitions=["hello", "greetings", "welcome"],
            examples=[
                ("Ndewo, kedu ka i mere?", "Hello, how are you?"),
                ("Ndewo nne m", "Greetings, my mother")
            ],
            dialects={"owa": "ndeewo", "onitsha": "ndewo"}
        ),
        "kedu": IgboWord(
            word="kedu",
            pronunciation="ke-du",
            part_of_speech="interjection",
            definitions=["how", "what about"],
            examples=[
                ("Kedu ka i mere?", "How are you?"),
                ("Kedu aha gị?", "What is your name?")
            ]
        ),
        "biko": IgboWord(
            word="biko",
            pronunciation="bi-ko",
            part_of_speech="adverb",
            definitions=["please", "I beg you"],
            examples=[
                ("Biko nyere m aka", "Please help me"),
                ("Biko bịa", "Please come")
            ]
        ),
        "daalụ": IgboWord(
            word="daalụ",
            pronunciation="da-a-lụ",
            part_of_speech="interjection",
            definitions=["thank you", "thanks"],
            examples=[
                ("Daalụ nne m", "Thank you, my mother"),
                ("Daalụ maka enyemaka gị", "Thanks for your help")
            ],
            dialects={"standard": "daalụ", "owa": "dalu"}
        ),
        "mmiri": IgboWord(
            word="mmiri",
            pronunciation="mmi-ri",
            part_of_speech="noun",
            definitions=["water", "rain"],
            examples=[
                ("Mmiri na-adọ", "The water is cold"),
                ("Mmiri na-ada", "It is raining")
            ],
            related_words=["mmiri ozuzo (rain)", "mmiri ọṅụṅụ (drinking water)"]
        ),
        "ala": IgboWord(
            word="ala",
            pronunciation="a-la",
            part_of_speech="noun",
            definitions=["land", "earth", "ground", "country"],
            examples=[
                ("Ala Igbo", "Igbo land"),
                ("Ala bụ nne", "The earth is mother")
            ],
            related_words=["ala nne (motherland)", "ala nna (fatherland)"]
        ),
        "ife": IgboWord(
            word="ife",
            pronunciation="i-fe",
            part_of_speech="noun",
            definitions=["light", "brightness", "thing"],
            examples=[
                ("Ife na-acha ọcha", "White light"),
                ("Ife ọ bụla", "Anything")
            ],
            dialects={"owa": "ife", "onitsha": "ivu"}
        ),
        "ụmụ": IgboWord(
            word="ụmụ",
            pronunciation="ụ-mụ",
            part_of_speech="noun",
            definitions=["children", "people of"],
            examples=[
                ("Ụmụ Igbo", "Igbo people/children"),
                ("Ụmụaka", "Children")
            ],
            related_words=["ụmụnna (kinsmen)", "ụmụnwanyị (women)"]
        )
    }
    
    # Common phrases
    PHRASES = {
        "greetings": [
            ("Ndewo", "Hello"),
            ("Kedu ka i mere?", "How are you?"),
            ("Ọ dị m mma, daalụ", "I'm fine, thank you"),
            ("Ka ọ dị", "Goodbye"),
            ("Ka emesia", "See you later"),
            ("Jisie ike", "Well done / Keep it up")
        ],
        "polite": [
            ("Biko", "Please"),
            ("Daalụ", "Thank you"),
            ("Chei, daalụ", "Oh, thank you"),
            ("Biko gbaghara m", "Please forgive me"),
            ("E meela", "Well done / Thank you")
        ],
        "family": [
            ("Nne m", "My mother"),
            ("Nna m", "My father"),
            ("Ụmụnne m", "My siblings"),
            ("Nwa m", "My child"),
            ("Di m", "My husband"),
            ("Nwunye m", "My wife")
        ],
        "numbers": [
            ("otu", "one"),
            ("abụọ", "two"),
            ("atọ", "three"),
            ("anọ", "four"),
            ("ise", "five"),
            ("isii", "six"),
            ("asaa", "seven"),
            ("asatọ", "eight"),
            ("iteghete", "nine"),
            ("iri", "ten")
        ]
    }
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the Igbo knowledge base.
        
        Args:
            data_dir: Optional directory for additional data files
        """
        self.data_dir = data_dir
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
    
    def get_proverb(self, category: str = None) -> Optional[IgboProverb]:
        """Get a random proverb, optionally filtered by category."""
        proverbs = self.PROVERBS
        if category:
            proverbs = [p for p in proverbs if p.category == category]
        
        if proverbs:
            import random
            return random.choice(proverbs)
        return None
    
    def search_proverbs(self, query: str) -> List[IgboProverb]:
        """Search proverbs by keyword."""
        query_lower = query.lower()
        results = []
        for proverb in self.PROVERBS:
            if (query_lower in proverb.igbo.lower() or
                query_lower in proverb.english.lower() or
                query_lower in proverb.meaning.lower()):
                results.append(proverb)
        return results
    
    def get_word(self, word: str) -> Optional[IgboWord]:
        """Get a word definition."""
        return self.VOCABULARY.get(word.lower())
    
    def search_words(self, query: str) -> List[IgboWord]:
        """Search vocabulary by keyword."""
        query_lower = query.lower()
        results = []
        for word_obj in self.VOCABULARY.values():
            if (query_lower in word_obj.word.lower() or
                any(query_lower in d.lower() for d in word_obj.definitions)):
                results.append(word_obj)
        return results
    
    def get_cultural_concept(self, concept: str) -> Optional[Dict]:
        """Get a cultural concept definition."""
        return self.CULTURAL_CONCEPTS.get(concept.lower())
    
    def get_phrases(self, category: str = None) -> List[Tuple[str, str]]:
        """Get phrases, optionally filtered by category."""
        if category:
            return self.PHRASES.get(category, [])
        all_phrases = []
        for phrases in self.PHRASES.values():
            all_phrases.extend(phrases)
        return all_phrases
    
    def detect_igbo(self, text: str) -> float:
        """
        Detect if text contains Igbo language.
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        # Check for known Igbo words
        igbo_word_count = 0
        for word in words:
            # Remove punctuation
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in self.VOCABULARY:
                igbo_word_count += 1
            # Check for common Igbo markers
            elif any(marker in clean_word for marker in ['chi', 'ala', 'nne', 'nna', 'ụmụ', 'ndị']):
                igbo_word_count += 0.5
        
        if len(words) == 0:
            return 0.0
        
        return min(igbo_word_count / len(words), 1.0)


class IgboLanguageExpert:
    """
    Specialized expert for Igbo language processing.
    
    Capabilities:
    - Translation (Igbo ↔ English)
    - Cultural context explanation
    - Proverb interpretation
    - Language learning assistance
    - Dialect awareness
    """
    
    def __init__(self, knowledge_base: IgboKnowledgeBase = None):
        """
        Initialize the Igbo language expert.
        
        Args:
            knowledge_base: Optional knowledge base instance
        """
        self.kb = knowledge_base or IgboKnowledgeBase()
        self.name = "igbo-language"
        self.modality = "text"
        self.specialties = ["igbo", "culture", "translation", "proverbs"]
    
    def process(self, query: str, context: list = None) -> str:
        """
        Process a query related to Igbo language or culture.
        
        Args:
            query: Input query
            context: Optional conversation context
            
        Returns:
            Response with Igbo language/cultural information
        """
        query_lower = query.lower()
        
        # Check for proverb request
        if any(kw in query_lower for kw in ['proverb', 'ilu', 'saying']):
            return self._handle_proverb_query(query)
        
        # Check for translation request
        if any(kw in query_lower for kw in ['translate', 'pịgharịa', 'meaning of']):
            return self._handle_translation_query(query)
        
        # Check for cultural concept
        if any(kw in query_lower for kw in ['culture', 'omenala', 'tradition', 'chi', 'ndichie']):
            return self._handle_culture_query(query)
        
        # Check for greeting
        if any(kw in query_lower for kw in ['ndewo', 'kedu', 'hello', 'greeting']):
            return self._handle_greeting(query)
        
        # Check for word definition
        return self._handle_definition_query(query)
    
    def _handle_proverb_query(self, query: str) -> str:
        """Handle proverb-related queries."""
        # Try to get a specific proverb
        proverbs = self.kb.search_proverbs(query)
        
        if proverbs:
            proverb = proverbs[0]
            return f"""**Igbo Proverb (Il Igbo):**
> {proverb.igbo}

**English Translation:**
> {proverb.english}

**Meaning:**
{proverb.meaning}

**Context:** {proverb.context}
**Category:** {proverb.category}
"""
        else:
            # Return a random proverb
            proverb = self.kb.get_proverb()
            if proverb:
                return f"""Here's an Igbo proverb for you:

**{proverb.igbo}**
*{proverb.english}*

Meaning: {proverb.meaning}

Would you like to hear more Igbo proverbs (ilu)?"""
        
        return "I don't have a specific proverb for that. Try asking about 'Igbo proverbs' or 'ilu' for some examples."
    
    def _handle_translation_query(self, query: str) -> str:
        """Handle translation queries."""
        # Extract the word to translate
        words = query.split()
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            word_obj = self.kb.get_word(clean_word)
            if word_obj:
                examples = "\n".join([
                    f"- {igbo}: {english}" 
                    for igbo, english in word_obj.examples[:2]
                ])
                return f"""**{word_obj.word}** ({word_obj.part_of_speech})
*Pronunciation: {word_obj.pronunciation}*

**Definitions:**
{chr(10).join('- ' + d for d in word_obj.definitions)}

**Examples:**
{examples}
"""
        
        return "I can help translate between Igbo and English. Please provide a specific word or phrase."
    
    def _handle_culture_query(self, query: str) -> str:
        """Handle cultural concept queries."""
        # Check for specific concepts
        for concept in self.kb.CULTURAL_CONCEPTS:
            if concept in query.lower():
                info = self.kb.get_cultural_concept(concept)
                if info:
                    return f"""**{concept.upper()}**

**Definition:** {info['definition']}

**Significance:** {info['significance']}

**Usage:** {info['usage']}
"""
        
        # General culture response
        return """Igbo culture (Omenala Igbo) is rich with traditions, philosophy, and wisdom.

Key concepts include:
- **Chi** - Personal spiritual guide
- **Omenala** - Tradition and custom
- **Ndichie** - Ancestors
- **Igwebuike** - Unity is strength
- **Ala** - Land/Earth

Would you like to learn about any specific aspect of Igbo culture?"""
    
    def _handle_greeting(self, query: str) -> str:
        """Handle greeting queries."""
        phrases = self.kb.get_phrases("greetings")
        polite = self.kb.get_phrases("polite")
        
        return f"""**Igbo Greetings (Ekele Igbo):**

{chr(10).join(f'- **{igbo}**: {english}' for igbo, english in phrases)}

**Polite Expressions:**

{chr(10).join(f'- **{igbo}**: {english}' for igbo, english in polite[:3])}

Ndewo! Kedu ka i mere? (Hello! How are you?)
"""
    
    def _handle_definition_query(self, query: str) -> str:
        """Handle word definition queries."""
        # Search for words in the query
        words = self.kb.search_words(query)
        
        if words:
            word = words[0]
            examples = "\n".join([
                f"- {igbo}: {english}" 
                for igbo, english in word.examples[:2]
            ])
            return f"""**{word.word}** ({word.part_of_speech})
*Pronunciation: {word.pronunciation}*

**Definitions:**
{chr(10).join('- ' + d for d in word.definitions)}

**Examples:**
{examples}
"""
        
        # Check if query contains Igbo
        confidence = self.kb.detect_igbo(query)
        if confidence > 0.3:
            return "I detect Igbo language in your query. How can I help you with Igbo language or culture today? You can ask about proverbs (ilu), translations, or cultural concepts (omenala)."
        
        return "I'm the Igbo Language Expert. I can help you with:\n- Igbo proverbs (ilu) and their meanings\n- Translations between Igbo and English\n- Cultural concepts (omenala, chi, ndichie)\n- Igbo vocabulary and phrases\n\nKedu ihe m ga-enyere gị aka? (How can I help you?)"
    
    def get_proverb_for_context(self, context: str) -> Optional[IgboProverb]:
        """Get a proverb relevant to a given context."""
        return self.kb.get_proverb()
    
    def translate_igbo_to_english(self, text: str) -> str:
        """Translate Igbo text to English."""
        # Simple word-by-word translation
        words = text.split()
        translated = []
        
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            word_obj = self.kb.get_word(clean_word)
            if word_obj:
                translated.append(word_obj.definitions[0])
            else:
                translated.append(word)
        
        return " ".join(translated)
    
    def explain_cultural_context(self, text: str) -> str:
        """Explain the cultural context of Igbo text."""
        concepts_found = []
        
        for concept in self.kb.CULTURAL_CONCEPTS:
            if concept in text.lower():
                info = self.kb.get_cultural_concept(concept)
                concepts_found.append(f"**{concept}**: {info['definition']}")
        
        if concepts_found:
            return "Cultural context:\n\n" + "\n\n".join(concepts_found)
        
        return "No specific cultural concepts found in the text."
    
    def get_status(self) -> Dict:
        """Get expert status."""
        return {
            "name": self.name,
            "modality": self.modality,
            "specialties": self.specialties,
            "proverbs_count": len(self.kb.PROVERBS),
            "vocabulary_count": len(self.kb.VOCABULARY),
            "cultural_concepts_count": len(self.kb.CULTURAL_CONCEPTS)
        }
