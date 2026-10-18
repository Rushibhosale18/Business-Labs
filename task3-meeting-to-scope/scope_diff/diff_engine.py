"""
Scope Diff Engine for Task 3.
Compares a follow-up meeting (Meeting C) against an approved baseline (Meeting A).
Identifies Added, Removed, Modified, and Out-of-Scope items.
"""
from typing import Dict, List, Any

class ScopeDiffEngine:
    def compare_scopes(self, baseline_reqs: List[Dict[str, Any]], followup_reqs: List[Dict[str, Any]]) -> Dict[str, Any]:
        baseline_map = {r["id"]: r for r in baseline_reqs}
        followup_map = {r["id"]: r for r in followup_reqs}
        
        added = []
        removed = []
        modified = []
        out_of_scope = []
        
        # Check follow-up items
        for r_id, r in followup_map.items():
            if r.get("is_out_of_scope"):
                out_of_scope.append({
                    "id": r_id,
                    "title": r["title"],
                    "description": r["description"],
                    "reason": r.get("scope_note", "Exceeds approved platform and budget boundaries. Requires separate proposal.")
                })
            elif r_id not in baseline_map:
                added.append({
                    "id": r_id,
                    "title": r["title"],
                    "description": r["description"],
                    "estimated_likely_hours": r.get("hours_likely", 0.0),
                    "reason": r.get("reason", "Newly requested in follow-up session.")
                })
            else:
                base_r = baseline_map[r_id]
                # Compare text or status
                if r.get("hours_likely") != base_r.get("hours_likely") or r.get("timeline") != base_r.get("timeline") or r.get("description") != base_r.get("description"):
                    modified.append({
                        "id": r_id,
                        "title": r["title"],
                        "original": base_r.get("description"),
                        "revised": r.get("description"),
                        "timeline_change": f"{base_r.get('timeline', 'N/A')} -> {r.get('timeline', 'N/A')}",
                        "hours_diff": r.get("hours_likely", 0.0) - base_r.get("hours_likely", 0.0)
                    })
                    
        # Check removed items
        for r_id, base_r in baseline_map.items():
            if r_id not in followup_map or followup_map[r_id].get("status") == "REMOVED":
                removed.append({
                    "id": r_id,
                    "title": base_r["title"],
                    "description": base_r["description"],
                    "saved_likely_hours": base_r.get("hours_likely", 0.0),
                    "reason": "Client confirmed removal to reduce budget/timeline."
                })

        baseline_likely_total = sum(r.get("hours_likely", 0.0) for r in baseline_reqs if r.get("status") != "REMOVED")
        added_hours = sum(r.get("estimated_likely_hours", 0.0) for r in added)
        removed_hours = sum(r.get("saved_likely_hours", 0.0) for r in removed)
        modified_hours_delta = sum(r.get("hours_diff", 0.0) for r in modified)
        
        revised_likely_total = baseline_likely_total + added_hours - removed_hours + modified_hours_delta

        return {
            "baseline_version": "v1.0 (Meeting A Approved Baseline)",
            "followup_version": "v1.1 (Meeting C Revision)",
            "summary": {
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified),
                "out_of_scope_count": len(out_of_scope),
                "original_likely_hours": baseline_likely_total,
                "net_hours_delta": round(revised_likely_total - baseline_likely_total, 1),
                "revised_likely_hours": round(revised_likely_total, 1)
            },
            "added_items": added,
            "removed_items": removed,
            "modified_items": modified,
            "out_of_scope_flags": out_of_scope
        }
