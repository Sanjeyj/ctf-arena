"""
AttackPathService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Models attack vectors by traversing network links, dependencies, and trust boundaries.
"""
from app.extensions import db
from app.models.exposure_asset import ExposureAsset
from app.models.attack_path import AttackPath
from app.models.service_dependency import ServiceDependency
from app.models.universe_link import UniverseLink
from app.services.exposure_inventory_service import ExposureInventoryService
from app.services.hook_service import HookService
import json
import datetime


class AttackPathService:

    @staticmethod
    def build_graph(org_id):
        # Fetch assets
        assets = ExposureAsset.query.filter_by(organization_id=org_id).all()
        asset_ids = {a.id for a in assets}
        asset_by_ref = {(a.asset_reference_type, a.asset_reference_id): a.id for a in assets}

        adj = {aid: set() for aid in asset_ids}

        # 1. Connect via ServiceDependencies (platform_services)
        try:
            deps = ServiceDependency.query.filter_by(organization_id=org_id).all()
            for d in deps:
                src_aid = asset_by_ref.get(('platform_service', d.source_service_id))
                tgt_aid = asset_by_ref.get(('platform_service', d.target_service_id))
                if src_aid and tgt_aid:
                    adj[src_aid].add(tgt_aid)
        except Exception:
            pass

        # 2. Connect via UniverseLinks (universe_nodes)
        try:
            links = UniverseLink.query.filter_by(organization_id=org_id).all()
            for l in links:
                src_aid = asset_by_ref.get(('universe_node', l.source_node_id))
                tgt_aid = asset_by_ref.get(('universe_node', l.target_node_id))
                if src_aid and tgt_aid:
                    adj[src_aid].add(tgt_aid)
        except Exception:
            pass

        # 3. Add default neighbors for testing paths
        # If asset A has zone public and asset B has zone application, add link
        for a in assets:
            for b in assets:
                if a.id != b.id:
                    # Public to Edge, Edge to Application, Application to Data
                    if a.architecture_zone and b.architecture_zone:
                        az = a.architecture_zone.zone_type
                        bz = b.architecture_zone.zone_type
                        if (az == 'public' and bz == 'edge') or \
                           (az == 'edge' and bz == 'application') or \
                           (az == 'application' and bz == 'data'):
                            adj[a.id].add(b.id)

        return adj

    @staticmethod
    def calculate_paths(source_id, target_id, org_id, max_depth=5):
        adj = AttackPathService.build_graph(org_id)
        if source_id not in adj or target_id not in adj:
            return []

        # DFS with cycle protection
        all_paths = []

        def dfs(curr, target, path, visited):
            if curr == target:
                all_paths.append(list(path))
                return
            if len(path) > max_depth:
                return

            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, target, path, visited)
                    path.pop()
                    visited.remove(neighbor)

        dfs(source_id, target_id, [source_id], {source_id})
        return all_paths

    @staticmethod
    def score_path(path_list, org_id):
        total_score = 0.0
        for aid in path_list:
            score = ExposureInventoryService.calculate_exposure_score(aid, org_id)
            total_score += score
        return round(total_score, 2)

    @staticmethod
    def find_critical_path(source_id, target_id, org_id):
        paths = AttackPathService.calculate_paths(source_id, target_id, org_id)
        if not paths:
            return None

        critical_path = None
        max_score = -1.0

        for p in paths:
            score = AttackPathService.score_path(p, org_id)
            if score > max_score:
                max_score = score
                critical_path = p

        if critical_path:
            # Check for hook register mutation
            hook_results = HookService.trigger_hook(
                'before_attack_path_analysis',
                source_id=source_id,
                target_id=target_id,
                path=critical_path,
                risk_score=max_score,
                org_id=org_id
            )
            for res in hook_results:
                if isinstance(res, dict):
                    max_score = res.get('risk_score', max_score)

            # Store computed path in the database
            name = f"Path from {source_id} to {target_id}"
            ap = AttackPath(
                name=name,
                source_asset_id=source_id,
                target_asset_id=target_id,
                path_json=json.dumps(critical_path),
                hop_count=len(critical_path) - 1,
                path_risk_score=max_score,
                organization_id=org_id
            )
            db.session.add(ap)
            db.session.commit()

            HookService.trigger_hook('after_attack_path_analysis', path_id=ap.id, org_id=org_id)
            return ap

        return None

    @staticmethod
    def explain_path(path_id, org_id):
        ap = AttackPath.query.filter_by(id=path_id, organization_id=org_id).first()
        if not ap:
            return "Path not found."

        hops = json.loads(ap.path_json or '[]')
        hop_names = []
        for h in hops:
            a = ExposureAsset.query.filter_by(id=h, organization_id=org_id).first()
            if a:
                hop_names.append(a.display_name)

        return f"Attack Path '{ap.name}' traverses through {ap.hop_count} hops: " + " -> ".join(hop_names) + f". Path Risk Score is {ap.path_risk_score}."

    @staticmethod
    def compare_paths(path_id_1, path_id_2, org_id):
        ap1 = AttackPath.query.filter_by(id=path_id_1, organization_id=org_id).first()
        ap2 = AttackPath.query.filter_by(id=path_id_2, organization_id=org_id).first()
        if not ap1 or not ap2:
            return "Cannot compare paths. One or both not found."

        diff = ap1.path_risk_score - ap2.path_risk_score
        status = "higher" if diff > 0 else "lower"
        return f"Path 1 risk score is {abs(round(diff, 2))} points {status} than Path 2."
