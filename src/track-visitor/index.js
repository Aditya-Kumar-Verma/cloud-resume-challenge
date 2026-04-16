import crypto from "crypto";
import { DynamoDBClient, UpdateItemCommand, PutItemCommand } from "@aws-sdk/client-dynamodb";

const ddb = new DynamoDBClient({});
const TABLE_PROFILES = process.env.TABLE_PROFILES;
const TABLE_EVENTS   = process.env.TABLE_EVENTS;

const GEO_API_IPAPI  = "https://ipapi.co";
const GEO_API_IPINFO = "https://ipinfo.io";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "OPTIONS,POST"
};

function hashVisitor(ip, ua) {
  return crypto.createHash("sha256").update(`${ip}-${ua}`).digest("hex");
}

// ⏱️ Helper for timeout fetch
async function fetchWithTimeout(url, options = {}, timeout = 2000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return await res.json();
  } finally {
    clearTimeout(id);
  }
}

export const handler = async (event) => {
  if (event.requestContext.http.method === "OPTIONS") {
    return { statusCode: 204, headers: CORS_HEADERS };
  }

  const ip =
    event.requestContext.http.sourceIp ||
    event.headers["x-forwarded-for"]?.split(",")[0];

  const body = JSON.parse(event.body || "{}");
  const ua = body.ua || event.headers["user-agent"] || "unknown";

  if (!ip) {
    return { statusCode: 400, headers: CORS_HEADERS, body: "IP missing" };
  }

  const visitorId = hashVisitor(ip, ua);

  // ✅ FIXED input handling
  let lat = body.lat !== undefined ? parseFloat(body.lat) : null;
  let lon = body.lon !== undefined ? parseFloat(body.lon) : null;

  let city = "Unknown";
  let country = "Unknown";

  try {
    // =========================================================
    // 🎯 1. PRECISE LOCATION (Browser)
    // =========================================================
    if (lat && lon && lat !== 0 && lon !== 0) {
      try {
        const geo = await fetchWithTimeout(
          `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
          {
            headers: {
              "User-Agent": "cloud-resume-challenge/1.0"
            }
          }
        );

        if (!geo || !geo.address) {
          throw new Error("Invalid reverse geo response");
        }

        city =
          geo.address.city ||
          geo.address.town ||
          geo.address.village ||
          geo.address.county ||
          "Unknown";

        country = geo.address.country || "Unknown";

      } catch (err) {
        console.error("Reverse geocode failed, falling back to IP", err);
        lat = null;
        lon = null;
      }
    }

    // =========================================================
    // 🌐 2. IP FALLBACK (if no precise location)
    // =========================================================
    if (lat === null || lon === null) {
      try {
        const geo = await fetchWithTimeout(`${GEO_API_IPAPI}/${ip}/json/`);

        if (!geo || geo.error || !geo.country_name) {
          throw new Error("ipapi failed");
        }

        lat = geo.latitude || 0;
        lon = geo.longitude || 0;
        city = geo.city || "Unknown";
        country = geo.country_name || "Unknown";

      } catch (err) {
        console.log("ipapi failed, trying ipinfo...");

        try {
          const data = await fetchWithTimeout(`${GEO_API_IPINFO}/${ip}/json`);

          if (!data || !data.loc) {
            throw new Error("ipinfo invalid");
          }

          const [latStr, lonStr] = data.loc.split(",");

          lat = parseFloat(latStr) || 0;
          lon = parseFloat(lonStr) || 0;
          city = data.city || "Unknown";
          country = data.country || "Unknown";

        } catch (err2) {
          console.error("Both IP APIs failed", err2);
          lat = 0;
          lon = 0;
        }
      }
    }

  } catch (err) {
    console.error("Geo resolution failed completely", err);
  }

  const now = new Date().toISOString();

  await ddb.send(new UpdateItemCommand({
    TableName: TABLE_PROFILES,
    Key: { visitor_id: { S: visitorId } },
    UpdateExpression:
      "SET visit_count = if_not_exists(visit_count, :zero) + :inc, last_seen = :now, city = :city, country = :country, lat = :lat, lon = :lon, user_agent = :ua",
    ExpressionAttributeValues: {
      ":zero": { N: "0" },
      ":inc": { N: "1" },
      ":now": { S: now },
      ":city": { S: city },
      ":country": { S: country },
      ":lat": { N: String(lat || 0) },
      ":lon": { N: String(lon || 0) },
      ":ua": { S: ua }
    }
  }));

  await ddb.send(new PutItemCommand({
    TableName: TABLE_EVENTS,
    Item: {
      event_id: { S: crypto.randomUUID() },
      visitor_id: { S: visitorId },
      timestamp: { S: now },
      ip: { S: ip },
      path: { S: body.path || "/" },
      referrer: { S: body.referrer || "" }
    }
  }));

  return {
    statusCode: 200,
    headers: CORS_HEADERS,
    body: JSON.stringify({ ok: true })
  };
};