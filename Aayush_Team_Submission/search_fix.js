/**
 * Patch for Excalidraw Issue #9503
 * Fix: Stabilize canvas search results order
 */

// Original buggy implementation (pseudo-code)
// export const searchElements = (elements, query) => {
//   return elements.filter(element => 
//     element.type === "text" && element.text.includes(query)
//   );
// };

// Fixed implementation
export const searchElements = (elements, query) => {
  const matchedElements = elements.filter(element => 
    element.type === "text" && element.text.includes(query)
  );

  // FIX: Sort elements by ID so the list remains stable 
  // even if their positions (x, y) change during dragging.
  return matchedElements.sort((a, b) => a.id.localeCompare(b.id));
};
