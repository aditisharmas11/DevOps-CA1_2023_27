# Excalidraw Issue #9503: Canvas Search Results Unstable

## Problem Statement
When searching for text on the canvas, the results list reorders itself unexpectedly when one of the matched elements is dragged around. This happens because React does not have a stable key to render the list, or the array of search results is not ordered consistently on every render when coordinates change.

## Proposed Fix
To stabilize the search results, we ensure that the list of elements returned by the search function is always sorted by a stable property, such as `element.id`. This prevents the React list from shuffling elements when their coordinates (or other non-stable properties) are updated during a drag event.

See `search_fix.js` for the implementation of the patch.
