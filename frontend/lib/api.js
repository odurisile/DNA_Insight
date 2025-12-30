export const BACKEND_URL = "http://127.0.0.1:5000";

export async function uploadSingleDNA(formData) {
  const res = await fetch(`${BACKEND_URL}/upload_dna`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function uploadParentsDNA(formData) {
  const res = await fetch(`${BACKEND_URL}/upload_parents`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function generatePDF(json) {
  const res = await fetch(`${BACKEND_URL}/generate_pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(json)
  });
  return await res.blob();
}
