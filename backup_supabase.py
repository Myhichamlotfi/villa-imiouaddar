#!/usr/bin/env python3
"""
Sauvegarde automatique des données Villa Imiouaddar (Supabase -> fichiers JSON).

Ce script est exécuté automatiquement chaque jour par GitHub Actions.
Il récupère les tables reservations, paiements et frais, et les enregistre
dans backups/YYYY-MM-DD.json afin de garder un historique récupérable.

Variables d'environnement requises (configurées en GitHub Secrets) :
  SUPABASE_URL          -> ex: https://lyuvxjzfncoywrnaqkdy.supabase.co
  SUPABASE_SERVICE_KEY  -> la clé "service_role" / "secret key" (jamais publique)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TABLES = ["reservations", "paiements", "frais"]


def fetch_table(table_name: str):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
    req = urllib.request.Request(url)
    req.add_header("apikey", SUPABASE_SERVICE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_SERVICE_KEY}")
    req.add_header("Accept", "application/json")

    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Erreur HTTP {resp.status} pour la table {table_name}")
        data = json.loads(resp.read().decode("utf-8"))
        return data


def main():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERREUR: variables SUPABASE_URL ou SUPABASE_SERVICE_KEY manquantes.")
        sys.exit(1)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    for table in TABLES:
        try:
            rows = fetch_table(table)
            snapshot["tables"][table] = rows
            print(f"OK  {table}: {len(rows)} lignes récupérées")
        except Exception as e:
            print(f"ERREUR sur la table {table}: {e}")
            snapshot["tables"][table] = {"error": str(e)}

    os.makedirs("backups", exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = os.path.join("backups", f"{today}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"Sauvegarde écrite dans {out_path}")

    # also maintain a 'latest.json' for quick access to the most recent backup
    latest_path = os.path.join("backups", "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
