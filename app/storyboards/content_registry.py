from typing import Dict, Callable, Optional
from app.models.schemas import Storyboard, StoryboardScene
from app.core.config import logger

# Drawing primitives registry mapping visual_type to render callbacks
DRAWING_REGISTRY: Dict[str, Callable] = {}

def register_drawer(visual_type: str):
    """
    Decorator to register a scene drawer function.
    """
    def decorator(func: Callable):
        DRAWING_REGISTRY[visual_type] = func
        logger.info(f"Registered visual drawer strategy: '{visual_type}'")
        return func
    return decorator

# Predefined hand-crafted fallback storyboards for the prototype chemistry queries
PH_SCALE_STORYBOARD = Storyboard(
    scenes=[
        StoryboardScene(
            visual_type="ph_scale_overview",
            script="The pH scale measures how acidic or basic a substance is, ranging from 0 to 14.",
            duration=6.0
        ),
        StoryboardScene(
            visual_type="acidic_solution",
            script="Solutions with a pH below 7 are acidic, containing a high concentration of hydrogen ions.",
            duration=7.0
        ),
        StoryboardScene(
            visual_type="basic_solution",
            script="Solutions with a pH above 7 are basic, with an abundance of hydroxide ions. Pure water sits neutral at exactly 7.",
            duration=8.0
        )
    ]
)

COVALENT_BOND_STORYBOARD = Storyboard(
    scenes=[
        StoryboardScene(
            visual_type="atoms_intro",
            script="Atoms seek stability by filling their outermost electron shells.",
            duration=6.0
        ),
        StoryboardScene(
            visual_type="electron_sharing",
            script="Non-metal atoms achieve this stability by sharing electrons with each other, forming a strong covalent link.",
            duration=7.0
        ),
        StoryboardScene(
            visual_type="molecule_formation",
            script="This shared pair of valence electrons binds the atoms together into a stable molecule, like water.",
            duration=7.0
        )
    ]
)

IONIC_VS_COVALENT_STORYBOARD = Storyboard(
    scenes=[
        StoryboardScene(
            visual_type="bond_comparison",
            script="Chemical bonds can be ionic or covalent, depending on how electrons behave.",
            duration=6.0
        ),
        StoryboardScene(
            visual_type="ionic_interaction",
            script="In ionic bonding, one atom transfers electrons to another, creating oppositely charged ions that attract.",
            duration=8.0
        ),
        StoryboardScene(
            visual_type="covalent_interaction",
            script="In covalent bonding, atoms share electrons instead of transferring them, holding them in a molecular pair.",
            duration=8.0
        )
    ]
)

def get_fallback_storyboard(query: str) -> Storyboard:
    """
    Finds and returns a hand-crafted storyboard for the required Chemistry topics.
    """
    q = query.lower().strip()
    if "ph scale" in q or "ph" in q:
        logger.info("Content Registry: Matching pH scale fallback storyboard.")
        return PH_SCALE_STORYBOARD
    elif "ionic" in q or "difference" in q:
        logger.info("Content Registry: Matching Ionic vs Covalent fallback storyboard.")
        return IONIC_VS_COVALENT_STORYBOARD
    elif "covalent bond" in q or "covalent bonding" in q or ("atoms" in q and "covalent" in q):
        logger.info("Content Registry: Matching Covalent bond fallback storyboard.")
        return COVALENT_BOND_STORYBOARD
    else:
        logger.warning(f"No specific fallback matched for query '{query}'. Returning default Covalent Bond storyboard.")
        return COVALENT_BOND_STORYBOARD
