"use client";

import { Download, ExternalLink } from "lucide-react";

interface Props {
  html: string;
  filename?: string;
}

export function CvHtmlPreview({ html, filename = "cv" }: Props) {
  function downloadPdf() {
    // The generated CV HTML embeds its own pixel-perfect html2pdf.js engine
    // (targeting #cv-page, with the photo zoom/pan controls hidden via
    // .no-print). Open it in a new tab and auto-click its download button —
    // this avoids SSR/bundling issues and image-quality loss from re-cloning
    // the document client-side.
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

  function openFullPreview() {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {/* PRIMARY: open in new tab and auto-trigger the embedded PDF download */}
        <button type="button" onClick={downloadPdf} className="btn-primary !px-4 !py-2 text-sm">
          <Download className="h-3.5 w-3.5" />
          Download PDF
        </button>

        {/* SECONDARY: open full A4 preview in new tab */}
        <button
          type="button"
          onClick={openFullPreview}
          className="btn-secondary !px-3 !py-1.5 text-xs"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Full preview
        </button>
      </div>

      {/* Inline preview iframe */}
      <div className="overflow-hidden rounded-xl border border-white/10 bg-white">
        <iframe
          srcDoc={html}
          sandbox="allow-scripts allow-downloads allow-popups"
          className="h-[600px] w-full"
          title="CV preview"
        />
      </div>
    </div>
  );
}
