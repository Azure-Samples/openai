// Utility functions for processing markdown in text

/**
 * Convert markdown formatting to HTML
 * Supports: **bold**, *italic*, numbered lists, bullet lists, links
 */
export function markdownToHTML(text: string): string {
  if (!text) return "";

  // First, fix concatenated numbered lists by adding line breaks
  // This handles cases like "1. Item A2. Item B3. Item C" -> "1. Item A\n2. Item B\n3. Item C"
  let processedText = text.replace(/(\d+\.\s+[^0-9]*?)(\d+\.\s+)/g, "$1\n$2");

  // Also handle bullet lists that might be concatenated
  processedText = processedText.replace(
    /([\-\*]\s+[^-*]*?)([\-\*]\s+)/g,
    "$1\n$2"
  );

  // Split text into lines to handle lists properly
  const lines = processedText.split("\n");
  const processedLines: string[] = [];
  let inOrderedList = false;
  let inUnorderedList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Check if this line is a numbered list item
    const numberedListMatch = line.match(/^\d+\.\s+(.*)$/);
    if (numberedListMatch) {
      if (!inOrderedList) {
        processedLines.push("<ol>");
        inOrderedList = true;
        inUnorderedList = false;
      }
      line = `<li>${numberedListMatch[1]}</li>`;
    }
    // Check if this line is a bullet list item
    else if (line.match(/^[\-\*]\s+(.*)$/)) {
      const bulletListMatch = line.match(/^[\-\*]\s+(.*)$/);
      if (bulletListMatch) {
        if (!inUnorderedList) {
          if (inOrderedList) {
            processedLines.push("</ol>");
            inOrderedList = false;
          }
          processedLines.push("<ul>");
          inUnorderedList = true;
        }
        line = `<li>${bulletListMatch[1]}</li>`;
      }
    }
    // Not a list item
    else {
      // Close any open lists
      if (inOrderedList) {
        processedLines.push("</ol>");
        inOrderedList = false;
      }
      if (inUnorderedList) {
        processedLines.push("</ul>");
        inUnorderedList = false;
      }

      // Process headers
      if (line.match(/^##### /))
        line = line.replace(/^##### (.*)$/, "<h5>$1</h5>");
      else if (line.match(/^#### /))
        line = line.replace(/^#### (.*)$/, "<h4>$1</h4>");
      else if (line.match(/^### /))
        line = line.replace(/^### (.*)$/, "<h3>$1</h3>");
      else if (line.match(/^## /))
        line = line.replace(/^## (.*)$/, "<h2>$1</h2>");
      else if (line.match(/^# /))
        line = line.replace(/^# (.*)$/, "<h1>$1</h1>");
    }

    // Process inline formatting
    line = line
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(
        /\[(.*?)\]\((.*?)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
      );

    processedLines.push(line);
  }

  // Close any remaining open lists
  if (inOrderedList) processedLines.push("</ol>");
  if (inUnorderedList) processedLines.push("</ul>");

  // Join lines with <br /> for line breaks (except for block elements)
  return processedLines
    .map((line, index) => {
      const nextLine = processedLines[index + 1];
      const isBlockElement =
        line.match(/^<(h[1-5]|ol|ul|\/ol|\/ul|li)/) ||
        line.match(/<\/(h[1-5]|ol|ul|li)>$/);
      const nextIsBlockElement =
        nextLine &&
        (nextLine.match(/^<(h[1-5]|ol|ul|\/ol|\/ul|li)/) ||
          nextLine.match(/<\/(h[1-5]|ol|ul|li)>$/));

      // Don't add <br /> after block elements or before block elements
      if (
        isBlockElement ||
        nextIsBlockElement ||
        index === processedLines.length - 1
      ) {
        return line;
      }
      return line + "<br />";
    })
    .join("");
}

/**
 * Check if text contains HTML tags
 */
export function isHTML(str: string): boolean {
  const div = document.createElement("div");
  div.innerHTML = str.trim();
  const childNodes = Array.from(div.childNodes);
  return (
    childNodes.length > 0 && childNodes.some((node) => node.nodeType === 1)
  );
}

/**
 * Legacy function for compatibility - lists are now handled in markdownToHTML
 */
export function wrapLists(html: string): string {
  return html;
}
