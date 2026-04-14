import boto3
import os
import json
from collections import defaultdict
from datetime import datetime

ssm = boto3.client("ssm")

def get_secret():
    name = os.environ.get("DASHBOARD_SECRET_NAME", "")
    if not name:
        return ""

    response = ssm.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return response["Parameter"]["Value"]

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Dashboard-Key"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": headers, "body": ""}

    provided_key = (event.get("headers") or {}).get("x-dashboard-key", "")
    actual_secret = get_secret()

    if provided_key != actual_secret:
        return {
            "statusCode": 401,
            "headers": headers,
            "body": json.dumps({"error": "Unauthorized"})
        }

    try:
        dynamodb = boto3.resource("dynamodb")
        profiles_table = dynamodb.Table(os.environ["TABLE_PROFILES"])
        events_table   = dynamodb.Table(os.environ["TABLE_EVENTS"])

        # Scan all visitor profiles
        profiles_resp = profiles_table.scan()
        profiles = profiles_resp.get("Items", [])
        while "LastEvaluatedKey" in profiles_resp:
            profiles_resp = profiles_table.scan(
                ExclusiveStartKey=profiles_resp["LastEvaluatedKey"]
            )
            profiles.extend(profiles_resp.get("Items", []))

        # Scan all events
        events_resp = events_table.scan()
        events = events_resp.get("Items", [])
        while "LastEvaluatedKey" in events_resp:
            events_resp = events_table.scan(
                ExclusiveStartKey=events_resp["LastEvaluatedKey"]
            )
            events.extend(events_resp.get("Items", []))

        # --- Aggregate ---
        total_unique   = len(profiles)
        total_visits   = sum(int(p.get("visit_count", 0)) for p in profiles)
        returning      = sum(1 for p in profiles if int(p.get("visit_count", 0)) > 1)
        new_visitors   = total_unique - returning

        # Country counts
        country_counts = defaultdict(int)
        city_counts    = defaultdict(int)
        lat_lon_list   = []

        for p in profiles:
            country = p.get("country", "Unknown")
            city    = p.get("city", "Unknown")
            visits  = int(p.get("visit_count", 0))
            country_counts[country] += visits
            city_counts[f"{city}, {country}"] += visits
            try:
                lat = float(p.get("lat", 0))
                lon = float(p.get("lon", 0))
                if lat != 0 or lon != 0:
                    lat_lon_list.append({
                        "lat": lat, "lon": lon,
                        "city": city, "country": country,
                        "visits": visits
                    })
            except (TypeError, ValueError):
                pass

        top_countries = sorted(
            [{"name": k, "visits": v} for k, v in country_counts.items()],
            key=lambda x: x["visits"], reverse=True
        )[:10]

        top_cities = sorted(
            [{"name": k, "visits": v} for k, v in city_counts.items()],
            key=lambda x: x["visits"], reverse=True
        )[:10]

        # Visits over time — group events by date
        daily_visits = defaultdict(int)
        for e in events:
            ts = e.get("timestamp", "")
            if ts:
                try:
                    date = ts[:10]  # YYYY-MM-DD
                    daily_visits[date] += 1
                except Exception:
                    pass

        visits_over_time = sorted(
            [{"date": k, "visits": v} for k, v in daily_visits.items()],
            key=lambda x: x["date"]
        )[-30:]  # last 30 days

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "total_unique":     total_unique,
                "total_visits":     total_visits,
                "returning":        returning,
                "new_visitors":     new_visitors,
                "top_countries":    top_countries,
                "top_cities":       top_cities,
                "visits_over_time": visits_over_time,
                "locations":        lat_lon_list
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }