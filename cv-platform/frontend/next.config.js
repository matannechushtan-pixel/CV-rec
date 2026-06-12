/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.supabase.co" },
    ],
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Prevent html2pdf.js (and its browser-only deps) from being bundled on the server
      config.externals = [
        ...(Array.isArray(config.externals) ? config.externals : []),
        "html2pdf.js",
        "html2canvas",
        "jspdf",
      ];
    }
    return config;
  },
};

module.exports = nextConfig;
