"""Rask test: logg inn på Garmin og hent golfdata."""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from app.garmin.client import garmin_client


async def main():
    print("1. Logger inn på Garmin Connect...")
    ok = await garmin_client.login()
    if not ok:
        print("   FEILET - sjekk credentials i .env")
        return

    print("   OK - innlogget!")

    print("\n2. Henter golfaktiviteter (siste 90 dager)...")
    activities = await garmin_client.get_golf_activities(days=90)
    print(f"   Fant {len(activities)} golfaktiviteter")

    if not activities:
        print("   Ingen golfaktiviteter funnet. Prøver alle aktivitetstyper...")
        from app.config import settings
        client = garmin_client._client
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")
        all_acts = client.get_activities_by_date(start, end)
        print(f"   Fant {len(all_acts)} aktiviteter totalt")
        for a in all_acts[:5]:
            print(f"   - {a.get('activityType', {}).get('typeKey', '?')}: {a.get('activityName')} ({a.get('startTimeLocal')})")
        return

    for a in activities[:3]:
        print(f"   - {a.get('activityName')} ({a.get('startTimeLocal')}) ID={a.get('activityId')}")

    print("\n3. Henter detaljer for siste aktivitet...")
    activity_id = str(activities[0]["activityId"])
    details = await garmin_client.get_activity_details(activity_id)
    if details:
        # Vis nøklene for å forstå datastrukturen
        print(f"   Nøkler i details: {list(details.keys())[:20]}")
        shots = details.get("golfShots", details.get("shots", []))
        print(f"   Antall slag funnet: {len(shots)}")
        if shots:
            print(f"   Første slag (nøkler): {list(shots[0].keys())}")
            print(f"   Første slag: {json.dumps(shots[0], indent=2, default=str)[:500]}")

    print("\n4. Bygger sessions...")
    sessions = await garmin_client.get_latest_sessions(limit=3)
    print(f"   Bygde {len(sessions)} sessions")
    for s in sessions:
        print(f"   - {s.date}: {s.club}, {s.summary.total_shots} slag, carry={s.summary.avg_carry_distance}")


asyncio.run(main())
