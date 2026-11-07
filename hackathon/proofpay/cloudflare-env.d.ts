declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    BUCKET?: R2Bucket;
    PAYPAL_CLIENT_ID?: string;
    PAYPAL_CLIENT_SECRET?: string;
    PAYPAL_MERCHANT_ID?: string;
    AI_API_KEY?: string;
    AI_BASE_URL?: string;
    AI_MODEL?: string;
  }
}
