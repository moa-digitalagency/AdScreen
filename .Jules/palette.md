## 2026-02-06 - Accessibility Gap in Navigation
**Learning:** Icon-only buttons (like mobile menu toggle and social links) were missing `aria-label` attributes, making them inaccessible to screen reader users. This was a critical gap in the primary navigation.
**Action:** Always verify icon-only interactive elements have an `aria-label` or `aria-labelledby` attribute. When using `<i>` tags for icons inside buttons/links, the container must carry the accessible name.
