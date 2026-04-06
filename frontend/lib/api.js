export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") || "http://127.0.0.1:5000";

async function parseResponse(res) {
  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const message =
      typeof payload === "string"
        ? payload
        : payload?.error || payload?.details || "Request failed";
    throw new Error(message);
  }

  return payload;
}

export async function uploadSingleDNA(formData) {
  const res = await fetch(`${BACKEND_URL}/upload_dna`, {
    method: "POST",
    body: formData
  });
  return parseResponse(res);
}

export async function uploadParentsDNA(formData) {
  const res = await fetch(`${BACKEND_URL}/upload_parents`, {
    method: "POST",
    body: formData
  });
  return parseResponse(res);
}

export async function generatePDF(json) {
  const res = await fetch(`${BACKEND_URL}/generate_pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(json)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "PDF generation failed");
  }
  return await res.blob();
}

export async function computeHeightPGS(formData) {
  const res = await fetch(`${BACKEND_URL}/height_pgs`, {
    method: "POST",
    body: formData
  });
  return parseResponse(res);
}

export async function lookupGene(formData) {
  const res = await fetch(`${BACKEND_URL}/gene_lookup`, {
    method: "POST",
    body: formData
  });
  return parseResponse(res);
}

export async function fetchGwasTraits(formData) {
  const res = await fetch(`${BACKEND_URL}/gwas_traits`, {
    method: "POST",
    body: formData
  });
  return parseResponse(res);
}
