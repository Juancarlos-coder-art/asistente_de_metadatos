from .dataframe_stats import DataFrameStatisticsExtractor
from .llm import LLMExtractor
from .static import StaticExtractor
from .structure import StructureExtractor
from .vocabulary import VocabularyMatcher

ALL_EXTRACTORS = [
    LLMExtractor,
    StaticExtractor,
    StructureExtractor,
    DataFrameStatisticsExtractor,
    VocabularyMatcher,
]
