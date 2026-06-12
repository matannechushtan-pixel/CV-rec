/**
 * Lightweight A4 HTML wrapper for exporting plain-text content (cover letters,
 * tailored CVs) to PDF via html2pdf.js, mirroring the approach used for
 * CV preview downloads in CvHtmlPreview.tsx.
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function buildTextPdfHtml(title: string, content: string): string {
  const safeBody = escapeHtml(content).replace(/\n/g, "<br />");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>${escapeHtml(title)}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
  body { margin: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background: #f1f5f9; }
  #page { width: 210mm; min-height: 297mm; margin: 16px auto; padding: 20mm; background: #fff; box-sizing: border-box; color: #1e293b; font-size: 12pt; line-height: 1.6; white-space: normal; }
  #download-btn { display: block; margin: 16px auto; padding: 10px 20px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }
</style>
</head>
<body>
<button id="download-btn" onclick="downloadPdf()">Download PDF</button>
<div id="page">${safeBody}</div>
<script>
  function downloadPdf() {
    var el = document.getElementById('page');
    var opt = {
      margin: 0,
      filename: ${JSON.stringify(title)} + '.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 3, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(el).save();
  }
</script>
</body>
</html>`;
}

export function openTextAsPdf(title: string, content: string) {
  const html = buildTextPdfHtml(title, content);
  const autoScript = `
    <script>
      window.addEventListener('load', function() {
        setTimeout(function() {
          var btn = document.getElementById('download-btn');
          if (btn) btn.click();
        }, 600);
      });
    <\/script>`;
  const modified = html.replace("</body>", autoScript + "</body>");
  const blob = new Blob([modified], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank", "noopener,noreferrer");
  if (!win) {
    alert("Please allow popups for this site to download the PDF.");
  }
  setTimeout(() => URL.revokeObjectURL(url), 120_000);
}
