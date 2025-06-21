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

/**
 * Converts a React component to a data URL
 * @param component The React component to convert
 * @param width The width of the resulting image (default: 1200)
 * @param height The height of the resulting image (default: 630)
 * @returns A promise that resolves to a data URL
 */
export const componentToDataUrl = async (
  component: React.ReactElement,
  width = 1200,
  height = 630
): Promise<string> => {
  // This is a simplified version - in a real app, you might want to use html-to-image or similar
  // For now, we'll return a blank data URL as a placeholder
  return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
};

/**
 * Triggers a print dialog for the current page
 */
export const triggerPrint = () => {
  window.print();
};
