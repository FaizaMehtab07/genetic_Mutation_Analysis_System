"""
NCBI E-utilities API Client - Live data fetching.

Communicates with NCBI to fetch real-time genetic data for ClinVar queries.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from backend.rag.sqlite_cache import sqlite_cache

logger = logging.getLogger(__name__)


class NCBIClient:
    """
    Client for NCBI E-utilities API.
    """

    EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
    ESUMMARY_URL = f"{EUTILS_BASE}/esummary.fcgi"
    CLINVAR_DB = "clinvar"

    def __init__(self, email: str, api_key: Optional[str] = None) -> None:
        self.email = email
        self.api_key = api_key
        self.logger = logging.getLogger("ncbi_client")
        self.session = requests.Session()
        self.rate_limit_delay = 0.34
        self.last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Respect NCBI rate limits."""

        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_clinvar(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search ClinVar for variants.
        """

        self.logger.info("Searching ClinVar: %s", query)

        try:
            self._rate_limit()
            params = {
                "db": self.CLINVAR_DB,
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "tool": "geneMutationDetection",
                "email": self.email,
            }
            if self.api_key:
                params["api_key"] = self.api_key

            response = self.session.get(self.ESEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "count": int(data.get("esearchresult", {}).get("count", 0)),
                "ids": data.get("esearchresult", {}).get("idlist", []),
                "query": query,
            }
        except Exception as exc:
            self.logger.error("Search failed: %s", str(exc))
            return {
                "success": False,
                "error": str(exc),
                "count": 0,
                "ids": [],
                "query": query,
            }

    def fetch_clinvar_details(self, variant_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed information about ClinVar variants.
        """

        if not variant_ids:
            return []

        self.logger.info("Fetching details for %s variants", len(variant_ids))

        try:
            self._rate_limit()
            params = {
                "db": self.CLINVAR_DB,
                "id": ",".join(variant_ids),
                "retmode": "json",
                "version": "2.0",
                "tool": "geneMutationDetection",
                "email": self.email,
            }
            if self.api_key:
                params["api_key"] = self.api_key

            response = self.session.get(self.ESUMMARY_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            result_block = data.get("result", {})
            uid_list = result_block.get("uids", variant_ids)
            variants = []
            for uid in uid_list:
                parsed = self._parse_clinvar_result(result_block.get(str(uid), {}), str(uid))
                if parsed:
                    variants.append(parsed)

            return variants
        except Exception as exc:
            self.logger.error("Fetch failed: %s", str(exc))
            return []

    def search_gene_variants(
        self,
        gene_symbol: str,
        pathogenic_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Search all variants in a gene.
        """

        query = f"{gene_symbol}[gene] AND clinvar[filter]"
        if pathogenic_only:
            query += " AND (pathogenic[clinical_significance] OR likely pathogenic[clinical_significance])"
        return self.search_clinvar(query, max_results=50)

    def _parse_clinvar_result(self, result: Dict[str, Any], uid: str) -> Dict[str, Any]:
        """
        Parse a single ClinVar summary result.
        """

        try:
            accession = (
                result.get("accession")
                or result.get("variation_set", [{}])[0].get("accession")
                or uid
            )

            genes = result.get("genes", [])
            gene = ""
            if genes and isinstance(genes, list):
                first_gene = genes[0]
                if isinstance(first_gene, dict):
                    gene = first_gene.get("symbol", "") or first_gene.get("gene_symbol", "")
                else:
                    gene = str(first_gene)

            condition = ""
            germline_classification = result.get("germline_classification", {})
            if isinstance(germline_classification, dict):
                condition = (
                    ", ".join(
                        item.get("trait_name", "")
                        for item in germline_classification.get("trait_set", [])
                        if isinstance(item, dict) and item.get("trait_name")
                    )
                )

            protein_change = ""
            protein_change_values = result.get("protein_change", [])
            if protein_change_values and isinstance(protein_change_values, list):
                protein_change = str(protein_change_values[0])

            clinical_significance = ""
            review_status = ""
            last_evaluated = ""
            if isinstance(germline_classification, dict):
                clinical_significance = germline_classification.get("description", "")
                review_status = germline_classification.get("review_status", "")
                last_evaluated = germline_classification.get("last_evaluated", "")

            variant_info = {
                "clinvar_id": str(accession),
                "protein_change": protein_change,
                "gene": gene,
                "condition": condition,
                "clinical_significance": clinical_significance,
                "review_status": review_status,
                "last_evaluated": last_evaluated,
                "variant_type": result.get("variant_type", ""),
            }
            return variant_info
        except Exception as exc:
            self.logger.warning("Error parsing result: %s", str(exc))
            return {}


class NCBIClientWithCache:
    """
    NCBI client with cache support to reduce API calls.
    """

    def __init__(self, email: str, api_key: Optional[str] = None, cache_ttl: int = 3600) -> None:
        self.client = NCBIClient(email, api_key)
        self.cache = sqlite_cache
        self.cache.cache_ttl = cache_ttl
        self.logger = logging.getLogger("ncbi_cached_client")

    def search_clinvar(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search with caching."""

        cache_key = f"ncbi_search:{query}:{max_results}"
        cached = self.cache.get_search_results(cache_key)
        if cached is not None:
            self.logger.debug("Cache hit: %s", query)
            return cached

        result = self.client.search_clinvar(query, max_results)
        self.cache.set_search_results(cache_key, result)
        return result

    def fetch_clinvar_details(self, variant_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch details with caching."""

        cached_results: List[Dict[str, Any]] = []
        missing_ids: List[str] = []

        for variant_id in variant_ids:
            cached = self.cache.get_variant_details(variant_id)
            if cached is not None:
                cached_results.append(cached)
            else:
                missing_ids.append(variant_id)

        if not missing_ids:
            self.logger.debug("Cache hit: %s variants", len(variant_ids))
            return cached_results

        fetched = self.client.fetch_clinvar_details(missing_ids)
        for item in fetched:
            variant_id = str(item.get("clinvar_id", ""))
            if variant_id:
                self.cache.set_variant_details(variant_id, item)

        return cached_results + fetched


__all__ = [
    "NCBIClient",
    "NCBIClientWithCache",
]
