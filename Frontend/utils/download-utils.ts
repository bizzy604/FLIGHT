/**
 * Utility functions for file downloads
 */

/**
 * Triggers a file download from a data URL
 * @param dataUrl The data URL to download
 * @param filename The name of the file to download
 */
export const downloadFromDataUrl = (dataUrl: string, filename: string) => {
  const link = document.createElement('a');
  link.href = dataUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Old componentToDataUrl function removed - now using generatePDFFromComponent for itinerary system

/**
 * Generate PDF from React component using browser print
 * @param elementId The ID of the element to convert to PDF
 * @param filename The name of the PDF file
 */
export const generatePDFFromComponent = async (elementId: string, filename: string = 'itinerary.pdf'): Promise<void> => {
  try {
    console.log(`🔍 Looking for element with ID: ${elementId}`);
    console.log(`📄 Filename: ${filename}`);

    const element = document.getElementById(elementId);
    if (!element) {
      console.error(`❌ Element with ID ${elementId} not found`);
      console.log(`🔍 Available elements with IDs:`,
        Array.from(document.querySelectorAll('[id]')).map(el => el.id).filter(id => id)
      );
      throw new Error(`Element with ID ${elementId} not found`);
    }

    console.log(`✅ Found element:`, element.tagName, element.className);

    console.log(`✅ Found element:`, element);
    console.log(`📏 Element dimensions: ${element.offsetWidth}x${element.offsetHeight}`);

    // Get the HTML content of the element
    const htmlContent = element.outerHTML;
    console.log(`📄 HTML content length: ${htmlContent.length} characters`);

    // Create a complete HTML document for PDF generation
    const fullHtmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>Flight Itinerary - ${filename}</title>
          <style>
            body {
              margin: 0;
              padding: 20px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              background: white;
              color: black;
              line-height: 1.5;
            }
            @page {
              size: A5;
              margin: 8mm;
            }
            @media print {
              body {
                margin: 0;
                padding: 5px;
                font-size: 11px !important;
                line-height: 1.2 !important;
              }
              .no-print { display: none !important; }
              .print-break {
                page-break-before: always !important;
                break-before: page !important;
              }
              /* Compact spacing for print */
              .min-h-\\[50vh\\] {
                min-height: auto !important;
              }
              /* Ensure proper page fitting */
              #official-itinerary {
                font-size: 11px !important;
                line-height: 1.2 !important;
              }
              /* Reduce margins and padding for print */
              .p-4 { padding: 8px !important; }
              .p-3 { padding: 6px !important; }
              .mb-4 { margin-bottom: 8px !important; }
              .mb-3 { margin-bottom: 6px !important; }
              .mb-2 { margin-bottom: 4px !important; }
              .gap-4 { gap: 8px !important; }
              .space-y-1 > * + * { margin-top: 2px !important; }
              .space-y-2 > * + * { margin-top: 4px !important; }
            }
            /* Include essential Tailwind classes for PDF */
            .bg-gradient-to-r { background: linear-gradient(to right, #dbeafe, #bfdbfe); }
            .bg-blue-50 { background-color: #eff6ff; }
            .bg-blue-100 { background-color: #dbeafe; }
            .bg-blue-600 { background-color: #2563eb; }
            .bg-gray-50 { background-color: #f9fafb; }
            .bg-gray-100 { background-color: #f3f4f6; }
            .bg-white { background-color: white; }
            .text-blue-600 { color: #2563eb; }
            .text-blue-800 { color: #1e40af; }
            .text-gray-600 { color: #4b5563; }
            .text-gray-700 { color: #374151; }
            .text-gray-800 { color: #1f2937; }
            .text-white { color: white; }
            .border { border: 1px solid #e5e7eb; }
            .border-b { border-bottom: 1px solid #e5e7eb; }
            .border-t { border-top: 1px solid #e5e7eb; }
            .border-blue-200 { border-color: #bfdbfe; }
            .border-gray-200 { border-color: #e5e7eb; }
            .border-gray-300 { border-color: #d1d5db; }
            .rounded-lg { border-radius: 0.5rem; }
            .rounded-full { border-radius: 9999px; }
            .p-3 { padding: 0.75rem; }
            .p-4 { padding: 1rem; }
            .p-6 { padding: 1.5rem; }
            .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
            .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
            .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
            .mb-2 { margin-bottom: 0.5rem; }
            .mb-4 { margin-bottom: 1rem; }
            .mb-6 { margin-bottom: 1.5rem; }
            .mt-4 { margin-top: 1rem; }
            .mt-6 { margin-top: 1.5rem; }
            .mr-2 { margin-right: 0.5rem; }
            .mr-3 { margin-right: 0.75rem; }
            .flex { display: flex; }
            .items-center { align-items: center; }
            .justify-between { justify-content: space-between; }
            .justify-center { justify-content: center; }
            .text-center { text-align: center; }
            .text-right { text-align: right; }
            .text-xs { font-size: 0.75rem; line-height: 1rem; }
            .text-sm { font-size: 0.875rem; }
            .text-lg { font-size: 1.125rem; }
            .text-xl { font-size: 1.25rem; }
            .text-2xl { font-size: 1.5rem; }
            .text-3xl { font-size: 1.875rem; }
            .leading-tight { line-height: 1.25; }
            .break-all { word-break: break-all; }
            .font-mono { font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace; }
            .font-bold { font-weight: 700; }
            .font-semibold { font-weight: 600; }
            .font-medium { font-weight: 500; }
            .uppercase { text-transform: uppercase; }
            .tracking-wide { letter-spacing: 0.025em; }
            .space-y-1 > * + * { margin-top: 0.25rem; }
            .space-y-2 > * + * { margin-top: 0.5rem; }
            .space-y-3 > * + * { margin-top: 0.75rem; }
            .space-y-4 > * + * { margin-top: 1rem; }
            .space-y-6 > * + * { margin-top: 1.5rem; }
            .space-x-4 > * + * { margin-left: 1rem; }
            .grid { display: grid; }
            .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
            .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .gap-4 { gap: 1rem; }
            .gap-6 { gap: 1.5rem; }
            .w-8 { width: 2rem; }
            .w-16 { width: 4rem; }
            .h-8 { height: 2rem; }
            .h-16 { height: 4rem; }
            .w-32 { width: 8rem; }
            .h-1 { height: 0.25rem; }
            .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
            .break-all { word-break: break-all; }
            .font-mono { font-family: ui-monospace, SFMono-Regular, monospace; }
          </style>
        </head>
        <body>
          ${htmlContent}
        </body>
      </html>
    `;

    // Open in new window and trigger print
    console.log(`🖨️ Opening print window for: ${filename}`);
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      console.log(`✅ Print window opened successfully`);
      printWindow.document.write(fullHtmlContent);
      printWindow.document.close();

      // Wait for content to load then print
      printWindow.onload = () => {
        console.log(`📄 Print window content loaded, triggering print...`);
        setTimeout(() => {
          printWindow.print();
          console.log(`🖨️ Print dialog triggered`);
        }, 500);
      };
    } else {
      console.log(`⚠️ Print window blocked, using fallback method`);
      // Fallback to current window print
      const originalContent = document.body.innerHTML;
      document.body.innerHTML = htmlContent;
      window.print();
      document.body.innerHTML = originalContent;
    }

  } catch (error) {
    console.error('❌ Error generating PDF:', error);
    console.error('❌ Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      type: typeof error
    });

    // Re-throw the error so the calling function can handle it properly
    throw error;
  }
};

// Old downloadComponentAsImage function removed - now using generatePDFFromComponent for itinerary system

/**
 * Triggers a print dialog for the current page
 */
export const triggerPrint = () => {
  window.print();
};
