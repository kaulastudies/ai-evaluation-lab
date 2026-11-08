import { getDatabase, getRuntimeConfiguration } from "../lib/proofpay/runtime";
export function getDb() { return getDatabase(getRuntimeConfiguration()); }
