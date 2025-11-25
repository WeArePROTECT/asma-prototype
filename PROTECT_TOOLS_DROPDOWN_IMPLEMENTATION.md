# PROTECT Tools Dropdown Implementation

**Date:** November 25, 2024  
**Feature:** Added PROTECT Tools dropdown menu to ASMA header navigation  
**Status:** ✅ Complete and deployed

---

## Overview

Added a dropdown menu button labeled "PROTECT Tools" to the ASMA prototype header navigation. This dropdown provides quick access to external PROTECT applications (File Viewer and GenomeDepot) for scientists using the ASMA platform.

## Files Changed

### `frontend/src/components/Header.tsx`

**What Changed:**
- Added React state management for dropdown open/close functionality
- Added dropdown button component in navigation area
- Implemented dropdown menu with two external links
- Added click-outside handler to close dropdown
- Added new styling function for dropdown menu items

**Why the Change Was Needed:**
Scientists using the ASMA platform need quick access to other PROTECT tools (File Viewer and GenomeDepot) without leaving the ASMA interface. This dropdown provides a centralized navigation point for accessing these external applications.

**How It Was Solved:**
1. **State Management:** Added `is_dropdown_open` state using `useState` to track dropdown visibility
2. **Ref for Click Detection:** Added `dropdown_ref` using `useRef` to detect clicks outside the dropdown
3. **Click-Outside Handler:** Implemented `useEffect` hook that listens for `mousedown` events outside the dropdown and closes it automatically
4. **Dropdown Button:** Created a button styled to match existing navigation links, positioned after "Formulate" button
5. **Dropdown Menu:** Implemented conditional rendering of dropdown menu with two links:
   - PROTECT File Viewer → `https://protect.qb3.berkeley.edu/protect/`
   - PROTECT GenomeDepot → `https://protect.qb3.berkeley.edu/genomedepot/`
6. **Styling:** Created `dropdownItemStyle()` function to maintain consistent styling with existing header design
7. **Security:** All external links use `target="_blank"` and `rel="noopener noreferrer"` for security

**Code Structure:**
- Uses snake_case naming convention (`is_dropdown_open`, `dropdown_ref`, `handle_click_outside`)
- Follows existing code patterns and styling approach
- Maintains consistency with existing header component structure

## Technical Details

### State Management
```typescript
const [is_dropdown_open, setIsDropdownOpen] = React.useState<boolean>(false);
const dropdown_ref = React.useRef<HTMLDivElement>(null);
```

### Click-Outside Detection
The dropdown automatically closes when clicking outside using a `useEffect` hook that:
- Adds a `mousedown` event listener when dropdown is open
- Checks if the click target is outside the dropdown ref
- Closes dropdown if click is outside
- Cleans up event listener when dropdown closes or component unmounts

### Styling
- Dropdown button matches existing nav link style using `linkStyle()` function
- Dropdown menu: white background, border, shadow, rounded corners
- Menu items have hover states with gray background (`#f3f4f6`)
- z-index set to 50 (above header content at 40, below modals)
- Positioned absolutely below button, aligned to right edge

### External Links
- Both links open in new tabs (`target="_blank"`)
- Security attributes included (`rel="noopener noreferrer"`)
- Dropdown closes automatically when a link is clicked

## Edge Cases Covered

1. **Click Outside:** Dropdown closes when clicking anywhere outside the dropdown area
2. **Click on Menu Item:** Dropdown closes when clicking a menu item (before navigation)
3. **Multiple Clicks:** Button toggles dropdown open/closed correctly
4. **Z-Index Management:** Dropdown appears above header content but below modals (z-index: 50)
5. **Viewport Overflow:** Dropdown is positioned to right edge to prevent overflow on small screens
6. **Event Cleanup:** Event listeners are properly removed to prevent memory leaks
7. **Type Safety:** All TypeScript types properly defined (boolean, HTMLDivElement, MouseEvent)

## Testing

### Manual Testing Performed
- ✅ Dropdown opens/closes on button click
- ✅ Dropdown closes when clicking outside
- ✅ Dropdown closes when clicking menu items
- ✅ Links open in new tabs correctly
- ✅ Hover states work on button and menu items
- ✅ Styling matches existing header design
- ✅ No console errors or warnings
- ✅ Works across different screen sizes

### Deployment
- ✅ Built new Docker image (`v0.0.9`)
- ✅ Deployed to production container (`asma-proto-v9`)
- ✅ Container running on port 8765
- ✅ Changes visible at `https://protect.qb3.berkeley.edu/asma/`

## User Experience

The dropdown provides a clean, intuitive way for scientists to access other PROTECT tools:
- **Discoverability:** Clearly labeled "PROTECT Tools" button in main navigation
- **Accessibility:** Standard dropdown pattern familiar to users
- **Efficiency:** Quick access without leaving ASMA interface
- **Visual Feedback:** Hover states and smooth transitions
- **Security:** External links open safely in new tabs

## Future Enhancements (Optional)

Potential improvements for future iterations:
- Add keyboard navigation support (arrow keys, Enter, Escape)
- Add icons to menu items for better visual recognition
- Add tooltips or descriptions for each tool
- Support for additional PROTECT tools as they become available
- Analytics tracking for tool usage

## Related Files

- `frontend/src/components/Header.tsx` - Main implementation file
- `Dockerfile` - Container build configuration (updated to v0.0.9)
- `compose.yml` - Container orchestration (reference only)

---

## Deployment Notes

**Container Information:**
- Image: `localhost/asma-prototype:v0.0.9`
- Container: `asma-proto-v9`
- Port: `8765:5000`
- Status: Running in production

**Build Command:**
```bash
podman build -t localhost/asma-prototype:v0.0.9 -f Dockerfile .
```

**Run Command:**
```bash
podman run -d --name asma-proto-v9 -p 8765:5000 \
  -v /opt/shared/spencerlong/asma-prototype/demo_data:/app/demo_data \
  -e ASMA_DATA_DIR=/app/demo_data \
  --restart unless-stopped \
  localhost/asma-prototype:v0.0.9
```

---

**Implementation completed by:** AI Assistant (Cursor)  
**Reviewed and approved by:** Spencer Long  
**Date:** November 25, 2024

