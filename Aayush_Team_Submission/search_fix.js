export const searchElements = (elements, query) => {
  const matchedElements = elements.filter(element => 
    element.type === "text" && element.text.includes(query)
  );

  return matchedElements.sort((a, b) => a.id.localeCompare(b.id));
};
