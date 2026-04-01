import crypto from "crypto";
import { DynamoDBClient, UpdateItemCommand, PutItemCommand } from "@aws-sdk/client-dynamodb";

const ddb = new DynamoDBClient({});
const TABLE_PROFILES = process.env.TABLE_PROFILES;
const TABLE_EVENTS = process.env.TABLE_EVENTS;
const GEO_API = "https://ipapi.co";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "OPTIONS,POST"
};

function hashVisitor(ip, ua) {
  return crypto.createHash("sha256").update(`${ip}-${ua}`).digest("hex");
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
    console.error("No IP found");
    return { statusCode: 400, headers: CORS_HEADERS, body: "IP missing" };
  }

  const visitorId = hashVisitor(ip, ua);

  let geo = {};
  try {
    const res = await fetch(`${GEO_API}/${ip}/json/`);
    geo = await res.json();
  } catch (err) {
    console.error("Geo lookup failed", err);
  }

  const now = new Date().toISOString();

  await ddb.send(new UpdateItemCommand({
    TableName: TABLE_PROFILES,
    Key: { visitor_id: { S: visitorId } },
    UpdateExpression: "SET visit_count = if_not_exists(visit_count, :zero) + :inc, last_seen = :now, city = :city, country = :country, lat = :lat, lon = :lon, user_agent = :ua",
    ExpressionAttributeValues: {
      ":zero": { N: "0" },
      ":inc": { N: "1" },
      ":now": { S: now },
      ":city": { S: geo.city || "Unknown" },
      ":country": { S: geo.country_name || "Unknown" },
      ":lat": { N: String(geo.latitude || 0) },
      ":lon": { N: String(geo.longitude || 0) },
      ":ua": { S: ua },
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