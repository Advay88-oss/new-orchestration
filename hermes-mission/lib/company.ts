/** The company the dashboard is looking at, shared by Brand Brain, Learning
 *  and What Vanna Can Do. The Assistant already stores its pick here. */

export const COMPANY_KEY = "vn_assistant_tenant";
export const COMPANY_EVENT = "vn-company";

export function readCompany(): string {
  try {
    return localStorage.getItem(COMPANY_KEY) || "";
  } catch {
    return "";
  }
}

export function writeCompany(tenant: string) {
  try {
    if (tenant) localStorage.setItem(COMPANY_KEY, tenant);
    else localStorage.removeItem(COMPANY_KEY);
  } catch { /* private mode */ }
  window.dispatchEvent(new CustomEvent(COMPANY_EVENT, { detail: tenant }));
}
