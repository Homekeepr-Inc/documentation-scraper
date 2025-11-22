from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class BrandConfig:
    brand: str
    display_name: str
    domains: List[str] = field(default_factory=list)
    additional_queries: List[str] = field(default_factory=list)
    max_candidates: int = 10

# The product(s) path does not contain an owner's manual PDF and should not be scraped.
SEARSPARTSDIRECT_QUERY_SUFFIX = '-inurl:"/product/" -inurl:"/products/"'


@dataclass
class ScraperStage:
    """Defines a SerpApi scraping stage with its preferred search domains."""

    name: str
    domains: List[str] = field(default_factory=list)
    query_suffix: str = ""


# Ordered scraper stages. Edit this list to change priority or add new scrapers.
SCRAPER_QUERY_STAGES: List[ScraperStage] = [
    ScraperStage(
        name="searspartsdirect",
        domains=["searspartsdirect.com"],
        query_suffix=SEARSPARTSDIRECT_QUERY_SUFFIX,
    ),
    ScraperStage(
        name="manualslib",
        domains=["manualslib.com"],
    ),
]


# Brand-specific configuration for query generation and scoring hints.
BRAND_CONFIGS: Dict[str, BrandConfig] = {
    "whirlpool": BrandConfig(
        brand="whirlpool",
        display_name="Whirlpool",
        domains=[
            # "whirlpool.com",
        ],
        additional_queries=[
            # "{brand} {model} tech sheet filetype:pdf",
            # "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
    "ge": BrandConfig(
        brand="ge",
        display_name="GE",
        domains=[
            # "geappliances.com",
            # "products.geappliances.com",
        ],
        additional_queries=[
            # "{brand} {model} owner's manual filetype:pdf",
            # "{brand} {model} service manual filetype:pdf",
        ],
    ),
    "lg": BrandConfig(
        brand="lg",
        display_name="LG",
        domains=[
            # "lg.com",
            # "lge.com",
        ],
        additional_queries=[
            # "{brand} {model} manual filetype:pdf",
            # "{brand} {model} owners manual filetype:pdf",
        ],
    ),
    "kitchenaid": BrandConfig(
        brand="kitchenaid",
        display_name="KitchenAid",
        domains=[
            # "kitchenaid.com",
        ],
        additional_queries=[
            # "{brand} {model} manual filetype:pdf",
            # "{brand} {model} quick start guide filetype:pdf",
        ],
    ),
    "samsung": BrandConfig(
        brand="samsung",
        display_name="Samsung",
        domains=[
            # "samsung.com",
            # "downloadcenter.samsung.com",
        ],
        additional_queries=[
            # "{brand} {model} user manual filetype:pdf",
            # "{brand} {model} installation manual filetype:pdf",
        ],
    ),
    "frigidaire": BrandConfig(
        brand="frigidaire",
        display_name="Frigidaire",
        domains=[
            # "frigidaire.com",
            # "electroluxmedia.com",
        ],
        additional_queries=[
            # "{brand} {model} owners manual filetype:pdf",
            # "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
    "aosmith": BrandConfig(
        brand="aosmith",
        display_name="AO Smith",
        domains=[
            # "hotwater.com",
            # "aosmith.com",
        ],
        additional_queries=[
            # "{brand} {model} manual filetype:pdf",
            # "{brand} {model} installation manual filetype:pdf",
        ],
    ),
    "rheem": BrandConfig(
        brand="rheem",
        display_name="Rheem",
        domains=[
            # "rheem.com",
            # "nwd.rheem.com",
        ],
        additional_queries=[
            # "{brand} {model} manual filetype:pdf",
            # "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
}

# Default fallbacks shared across brands.
DEFAULT_QUERY_TEMPLATES = [
    # "{brand} {model} owner's manual filetype:pdf",
    # "{brand} {model} manual filetype:pdf",
    # "{brand} {model} installation manual filetype:pdf",
    # "{model} owner's manual filetype:pdf",
    # "{model} manual filetype:pdf",
]


def get_brand_config(brand: str) -> BrandConfig:
    brand_lower = (brand or "").lower()
    if brand_lower in BRAND_CONFIGS:
        return BRAND_CONFIGS[brand_lower]
    display_name = brand.title() if brand else "Appliance"
    return BrandConfig(brand=brand_lower, display_name=display_name)


def build_stage_queries(
    config: BrandConfig,
    model: str,
    stage: ScraperStage,
) -> List[str]:
    """Construct SerpApi queries for a single scraper stage."""

    queries: List[str] = []
    normalized_model = model.strip()
    brand_model = " ".join(part for part in [config.display_name, normalized_model] if part)
    manual_phrase = "owner's manual"

    domains = [domain.strip() for domain in stage.domains if domain.strip()]
    if domains:
        for domain in domains:
            if brand_model:
                base_query = f"{brand_model} {manual_phrase} site:{domain}"
            else:
                base_query = f"{manual_phrase} site:{domain}"
            if stage.query_suffix:
                base_query = f"{base_query} {stage.query_suffix.strip()}"
            queries.append(base_query.strip())
    else:
        if brand_model:
            base_query = f"{brand_model} {manual_phrase}"
        else:
            base_query = manual_phrase
        if stage.query_suffix:
            base_query = f"{base_query} {stage.query_suffix.strip()}"
        queries.append(base_query.strip())

    deduped: List[str] = []
    seen = set()
    for query in queries:
        if query in seen:
            continue
        seen.add(query)
        deduped.append(query)

    return deduped[: max(1, config.max_candidates)]


def build_scraper_query_plan(
    config: BrandConfig,
    model: str,
    *,
    stages: Optional[List[ScraperStage]] = None,
) -> List[Tuple[ScraperStage, List[str]]]:
    """Return ordered (stage, queries) pairs describing the SerpApi search plan."""

    selected_stages = stages or SCRAPER_QUERY_STAGES
    plan: List[Tuple[ScraperStage, List[str]]] = []
    for stage in selected_stages:
        queries = build_stage_queries(config, model, stage)
        if queries:
            plan.append((stage, queries))
    return plan
