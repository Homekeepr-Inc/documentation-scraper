from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BrandConfig:
    brand: str
    display_name: str
    domains: List[str] = field(default_factory=list)
    additional_queries: List[str] = field(default_factory=list)
    max_candidates: int = 10


# Brand-specific configuration for query generation and scoring hints.
BRAND_CONFIGS: Dict[str, BrandConfig] = {
    "whirlpool": BrandConfig(
        brand="whirlpool",
        display_name="Whirlpool",
        domains=["whirlpool.com"],
        additional_queries=[
            "{brand} {model} tech sheet filetype:pdf",
            "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
    "ge": BrandConfig(
        brand="ge",
        display_name="GE",
        domains=["geappliances.com", "products.geappliances.com"],
        additional_queries=[
            "{brand} {model} owner's manual filetype:pdf",
            "{brand} {model} service manual filetype:pdf",
        ],
    ),
    "lg": BrandConfig(
        brand="lg",
        display_name="LG",
        domains=["lg.com", "lge.com"],
        additional_queries=[
            "{brand} {model} manual filetype:pdf",
            "{brand} {model} owners manual filetype:pdf",
        ],
    ),
    "kitchenaid": BrandConfig(
        brand="kitchenaid",
        display_name="KitchenAid",
        domains=["kitchenaid.com"],
        additional_queries=[
            "{brand} {model} manual filetype:pdf",
            "{brand} {model} quick start guide filetype:pdf",
        ],
    ),
    "samsung": BrandConfig(
        brand="samsung",
        display_name="Samsung",
        domains=["samsung.com", "downloadcenter.samsung.com"],
        additional_queries=[
            "{brand} {model} user manual filetype:pdf",
            "{brand} {model} installation manual filetype:pdf",
        ],
    ),
    "frigidaire": BrandConfig(
        brand="frigidaire",
        display_name="Frigidaire",
        domains=["frigidaire.com", "electroluxmedia.com"],
        additional_queries=[
            "{brand} {model} owners manual filetype:pdf",
            "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
    "aosmith": BrandConfig(
        brand="aosmith",
        display_name="AO Smith",
        domains=["hotwater.com", "aosmith.com"],
        additional_queries=[
            "{brand} {model} manual filetype:pdf",
            "{brand} {model} installation manual filetype:pdf",
        ],
    ),
    "rheem": BrandConfig(
        brand="rheem",
        display_name="Rheem",
        domains=["rheem.com", "nwd.rheem.com"],
        additional_queries=[
            "{brand} {model} manual filetype:pdf",
            "{brand} {model} installation instructions filetype:pdf",
        ],
    ),
}

# Default fallbacks shared across brands.
DEFAULT_QUERY_TEMPLATES = [
    "{brand} {model} owner's manual filetype:pdf",
    "{brand} {model} manual filetype:pdf",
    "{brand} {model} installation manual filetype:pdf",
    "{model} owner's manual filetype:pdf",
    "{model} manual filetype:pdf",
]


def get_brand_config(brand: str) -> BrandConfig:
    brand_lower = (brand or "").lower()
    if brand_lower in BRAND_CONFIGS:
        return BRAND_CONFIGS[brand_lower]
    display_name = brand.title() if brand else "Appliance"
    return BrandConfig(brand=brand_lower, display_name=display_name)


def build_queries(config: BrandConfig, model: str) -> List[str]:
    """Construct ordered list of search queries for a brand/model pair."""
    queries: List[str] = []
    normalized_model = model.strip()

    # Domain-targeted queries first.
    for domain in config.domains:
        domain = domain.strip()
        if not domain:
            continue
        queries.append(
            f"{config.display_name} {normalized_model} owner's manual filetype:pdf site:{domain}"
        )
        queries.append(
            f"{config.display_name} {normalized_model} manual filetype:pdf site:{domain}"
        )

    # Brand-specific templates.
    for template in config.additional_queries:
        queries.append(template.format(model=normalized_model, brand=config.display_name))

    # Shared templates.
    for template in DEFAULT_QUERY_TEMPLATES:
        queries.append(template.format(model=normalized_model, brand=config.display_name))

    # Deduplicate while preserving order.
    deduped: List[str] = []
    seen = set()
    for query in queries:
        if query in seen:
            continue
        seen.add(query)
        deduped.append(query)

    # Cap at a reasonable number to control SerpApi usage.
    return deduped[: max(1, config.max_candidates)]
