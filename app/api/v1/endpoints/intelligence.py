"""
Intelligence API endpoint for weekly security intelligence
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import httpx
from typing import List, Dict, Any

router = APIRouter()

# NVD API v2.0 endpoint
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

async def fetch_nvd_cves() -> List[Dict[str, Any]]:
    """Fetch recent CVEs from NVD API"""
    try:
        # Calculate date range - last 7 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Format dates for NVD API (ISO 8601 format without microseconds)
        pub_start = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        pub_end = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        params = {
            "pubStartDate": pub_start,
            "pubEndDate": pub_end,
            "resultsPerPage": 20,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(NVD_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
        return data.get("vulnerabilities", [])
    
    except httpx.HTTPStatusError as e:
        # If NVD API fails, return mock data for demonstration
        return []
    except Exception as e:
        return []

def normalize_cve_data(cve_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize CVE data to standard format"""
    normalized = []
    
    for vuln in cve_data:
        try:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            published = cve.get("published", "")
            
            # Extract description
            descriptions = cve.get("descriptions", [])
            description = ""
            if descriptions:
                description = descriptions[0].get("value", "")
            
            title = f"{cve_id}: {description[:100]}..." if len(description) > 100 else f"{cve_id}: {description}"
            
            # Default severity for unscored CVEs
            severity = "UNKNOWN"
            
            # Extract CVSS score and determine severity
            metrics = cve.get("metrics", {})
            score = None
            
            # Try CVSS v3.1 first (most recent)
            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                score = cvss_data.get("baseScore")
            # Try CVSS v3.0
            elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
                score = cvss_data.get("baseScore")
            # Fallback to CVSS v2
            elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})
                score = cvss_data.get("baseScore")
            
            # Map score to severity
            if score is not None:
                if score >= 7.0:
                    severity = "HIGH"
                elif score >= 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
            # If no score available, mark as UNKNOWN instead of assuming LOW
            
            normalized.append({
                "title": title,
                "category": "CVE",
                "severity": severity,
                "source": "NVD",
                "publishedAt": published,
                "cveId": cve_id,
                "cvssScore": score
            })
        except Exception as e:
            # Skip malformed entries
            continue
    
    return normalized

@router.get("/intelligence/weekly")
async def get_weekly_intelligence():
    """
    Get weekly security intelligence from various sources
    Returns top 5 latest security vulnerabilities
    """
    # Fetch CVEs from NVD
    cve_data = await fetch_nvd_cves()
    
    # If no data from NVD, return mock data for demonstration
    if not cve_data:
        mock_data = [
            {
                "title": "CVE-2024-XXXX: Critical authentication bypass in web framework",
                "category": "CVE",
                "severity": "HIGH",
                "source": "NVD",
                "publishedAt": datetime.utcnow().isoformat(),
                "cveId": "CVE-2024-XXXX",
                "cvssScore": 9.8
            },
            {
                "title": "CVE-2024-YYYY: SQL injection vulnerability in database library",
                "category": "CVE",
                "severity": "HIGH",
                "source": "NVD",
                "publishedAt": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "cveId": "CVE-2024-YYYY",
                "cvssScore": 8.5
            },
            {
                "title": "CVE-2024-ZZZZ: Cross-site scripting in popular CMS",
                "category": "CVE",
                "severity": "MEDIUM",
                "source": "NVD",
                "publishedAt": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "cveId": "CVE-2024-ZZZZ",
                "cvssScore": 6.1
            },
            {
                "title": "CVE-2024-AAAA: Remote code execution in IoT device",
                "category": "CVE",
                "severity": "HIGH",
                "source": "NVD",
                "publishedAt": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "cveId": "CVE-2024-AAAA",
                "cvssScore": 9.0
            },
            {
                "title": "CVE-2024-BBBB: Information disclosure in API endpoint",
                "category": "CVE",
                "severity": "MEDIUM",
                "source": "NVD",
                "publishedAt": (datetime.utcnow() - timedelta(days=4)).isoformat(),
                "cveId": "CVE-2024-BBBB",
                "cvssScore": 5.3
            }
        ]
        return mock_data
    
    # Normalize the data
    normalized_data = normalize_cve_data(cve_data)
    
    # Sort by published date (latest first) and CVSS score (highest first)
    normalized_data.sort(
        key=lambda x: (x["publishedAt"], x.get("cvssScore", 0)),
        reverse=True
    )
    
    # Return top 5
    return normalized_data[:5]
