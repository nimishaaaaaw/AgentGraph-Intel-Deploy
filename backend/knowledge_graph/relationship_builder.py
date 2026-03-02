"""
Relationship builder — infers relationships between entities and persists
them to Neo4j.
"""
import json
import re
from typing import List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)

_REL_PROMPT = """You are a knowledge graph builder. Given entities and source text, identify relationships between entities.

Entities:
{entities_json}

Source text:
{text}

IMPORTANT: You MUST respond with ONLY a valid JSON array. No markdown, no code fences, no explanation.

Each element must have exactly these keys:
- "source": entity name (must match an entity above exactly)
- "target": entity name (must match an entity above exactly)  
- "relationship": type in UPPER_SNAKE_CASE (e.g. IS_A, HAS_SKILL_IN, WORKED_ON, USES, PART_OF)
- "description": one sentence describing the relationship

Example response format:
[{{"source": "Alice", "target": "Google", "relationship": "WORKS_AT", "description": "Alice works at Google"}}]

Your response (ONLY the JSON array, nothing else):"""


class RelationshipBuilder:
    """Build and persist entity relationships."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        text: str,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Infer relationships between *entities* using the source *text*.

        Returns:
            List of relationship dicts:
            ``{"source": str, "target": str, "relationship": str, "description": str}``
        """
        if not entities or len(entities) < 2:
            return []

        try:
            return self._llm_build(text, entities)
        except Exception as exc:
            logger.warning("LLM relationship building failed (%s)", exc)
            return []

    def persist(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ) -> None:
        """
        Upsert entities and relationships into Neo4j.
        This is a best-effort operation — exceptions are logged but not raised.
        """
        try:
            from knowledge_graph.neo4j_client import Neo4jClient  # deferred

            client = Neo4jClient()
            self._upsert_entities(client, entities)
            self._upsert_relationships(client, relationships)
            logger.info(
                "Persisted %d entities and %d relationships to Neo4j",
                len(entities),
                len(relationships),
            )
        except Exception as exc:
            logger.warning("Neo4j persist failed: %s", exc)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _llm_build(
        self,
        text: str,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        from llm.llm_factory import LLMFactory  # deferred

        llm = LLMFactory.get_llm()
        prompt = _REL_PROMPT.format(
            entities_json=json.dumps(
                [{"name": e["name"], "type": e["type"]} for e in entities[:20]],
                indent=2,
            ),
            text=text[:2000],
        )
        raw = llm.generate(prompt)
        logger.debug("Relationship LLM raw response: %s", raw[:500])

        # Strip markdown code fences if present
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        # Try to find JSON array
        json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON array in LLM response")

        rels = json.loads(json_match.group())
        validated: List[Dict[str, Any]] = []
        entity_names = {e["name"] for e in entities}
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            src = str(rel.get("source", "")).strip()
            tgt = str(rel.get("target", "")).strip()
            rel_type = str(rel.get("relationship", "RELATED_TO")).upper().replace(" ", "_")
            if src and tgt and src != tgt:
                validated.append(
                    {
                        "source": src,
                        "target": tgt,
                        "relationship": rel_type,
                        "description": str(rel.get("description", "")),
                    }
                )
        logger.info("LLM built %d relationships", len(validated))
        return validated

    def _upsert_entities(
        self, client, entities: List[Dict[str, Any]]
    ) -> None:
        query = """
        UNWIND $entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.type = ent.type,
            e.description = ent.description,
            e.updated_at = timestamp()
        """
        client.run_write_query(query, {"entities": entities})

    def _upsert_relationships(
        self, client, relationships: List[Dict[str, Any]]
    ) -> None:
        for rel in relationships:
            # Dynamic relationship type requires a separate query per type
            query = f"""
            MATCH (a:Entity {{name: $source}})
            MATCH (b:Entity {{name: $target}})
            MERGE (a)-[r:{rel['relationship']}]->(b)
            SET r.description = $description,
                r.updated_at = timestamp()
            """
            try:
                client.run_write_query(
                    query,
                    {
                        "source": rel["source"],
                        "target": rel["target"],
                        "description": rel.get("description", ""),
                    },
                )
            except Exception as exc:
                logger.debug("Skipping relationship upsert: %s", exc)