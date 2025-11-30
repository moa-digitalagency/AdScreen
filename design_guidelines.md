# Design Guidelines - SaaS Location Écrans Publicitaires

## Design Approach

**Hybrid Approach**: Combining modern SaaS dashboard patterns (Linear, Stripe, Notion) for admin interfaces with intuitive booking platform patterns (Airbnb, Calendly) for the public client interface.

**Rationale**: The platform serves distinct user types with different needs—data-heavy dashboards for admins/establishments vs. frictionless booking experience for public clients.

## Typography

**Font Family**: 
- Primary: Inter (Google Fonts) - system UI, modern, excellent readability
- Monospace: JetBrains Mono - for technical specs, resolution displays, pricing

**Type Scale**:
- Headings: text-4xl (36px) to text-xl (20px), font-semibold to font-bold
- Body: text-base (16px), font-normal
- Small/Meta: text-sm (14px), text-xs (12px)
- Stats/Numbers: text-2xl to text-5xl, font-bold, tabular-nums

## Layout System

**Spacing Primitives**: Tailwind units of 1, 2, 4, 6, 8, 12, 16, 24
- Tight spacing: space-y-1, gap-2 (compact lists, form fields)
- Standard: space-y-4, gap-4, p-6 (cards, sections)
- Generous: space-y-8, gap-8, p-8 to p-12 (major sections)

**Grid System**:
- Dashboard: 12-column grid with sidebar (256px fixed) + main content area
- Cards/Stats: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4
- Forms: max-w-2xl centered, two-column layouts for related fields

## Core Components

### Navigation & Layout

**Superadmin/Establishment Dashboards**:
- Fixed sidebar (w-64): Logo top, navigation middle, user profile bottom
- Top bar: Breadcrumbs left, notifications/search/profile right, h-16
- Main content: max-w-7xl mx-auto, px-6 to px-8, py-8

**Public Client Interface**:
- Minimal top nav: Logo left, "Mes Réservations" link right, sticky
- Single-column flow: max-w-3xl mx-auto
- Mobile-first responsive design

**Player Interface**:
- Fullscreen black background
- Minimal controls: Login form centered, "Lancer Playlist" button bottom-right
- Status indicator: top-right corner (online/play/pause)

### Data Display

**Tables** (validation queue, stats, logs):
- Full-width with horizontal scroll on mobile
- Sticky header row
- Row hover states with clear actions (icon buttons right-aligned)
- Pagination: 10/25/50/100 items per page
- Search/filter bar above table

**Stats Cards**:
- Grid layout: 3-4 columns on desktop, stacked on mobile
- Icon + Label + Large Number + Trend indicator
- Border/shadow for separation, p-6 padding
- Hover lift effect (subtle)

**Calendar/Availability Grid**:
- Weekly/daily view toggle
- Time slots as grid cells (clickable, show availability %)
- Selected state clearly visible
- Legend for color coding (available/partial/full)

### Forms & Inputs

**Form Layout**:
- Label above input (font-medium, text-sm)
- Input fields: h-10 to h-12, px-4, rounded-lg
- Helper text below (text-xs, text-gray-600)
- Error states: red border + error message
- Field groups: space-y-4

**Upload Areas**:
- Drag-and-drop zone: border-2 border-dashed, p-12, rounded-lg
- File preview: thumbnail + metadata (size, resolution, duration)
- Progress bars during upload
- Validation feedback inline (checkmarks/warnings)

**Buttons**:
- Primary CTA: px-6, py-3, rounded-lg, font-semibold
- Secondary: outlined variant
- Icon buttons: w-10 h-10, rounded-full for actions
- Loading states with spinner

### Screen Management

**Screen Cards** (establishment dashboard):
- Grid layout: 2-3 columns on desktop
- Card structure: Image/icon top, name + specs, status indicator, action buttons bottom
- Quick stats: uptime %, revenue today
- QR code generation button prominent

**Screen Configuration**:
- Two-column layout: Specs left (resolution, orientation), Pricing right
- Slot configuration: table format with inline editing
- Time periods: visual timeline with coefficient multipliers
- Preview panel: live mockup of screen with sample content

### Booking Flow (Public Client)

**Step 1 - Screen Info**:
- Hero section: Screen photo/placeholder (h-64 to h-96)
- Specs grid: 2-3 columns (resolution, orientation, location)
- Availability calendar below

**Step 2 - Selection**:
- Sticky summary sidebar (desktop): Selected items + running total
- Mobile: bottom sheet with summary
- Content type toggles (image/video)
- Duration selector: button group or dropdown
- Time period chips: morning/afternoon/evening/night with pricing

**Step 3 - Upload**:
- Large upload zone with clear format requirements
- Real-time validation feedback
- Preview with overlay showing how it will display

**Step 4 - Payment**:
- Order summary: itemized list
- Stripe embedded form
- Trust indicators (secure payment icons)

### Content Validation (Establishment)

**Queue View**:
- List/grid toggle
- Each item: Thumbnail + metadata + Preview button + Approve/Reject actions
- Rejection modal: Reason selection (dropdown) + optional message
- Batch actions for multiple items

**Content Preview Modal**:
- Fullscreen overlay
- Content centered and scaled appropriately
- Metadata sidebar: duration, resolution, client info
- Approve/Reject buttons bottom

### Player Dashboard

**Login Screen**:
- Centered card (max-w-md): Logo, screen ID input, password, login button
- Fullscreen recommendation notice
- Clean, minimal design

**Playing State**:
- Fullscreen content display
- Minimal overlay (dismissible): Current content info, next up, time remaining
- Emergency pause button (small, corner)

## Responsive Strategy

**Breakpoints**:
- Mobile: base (< 768px) - single column, stacked navigation
- Tablet: md (768px+) - 2-column grids, persistent sidebar option
- Desktop: lg (1024px+) - full sidebar, 3+ column grids
- Large: xl (1280px+) - max content width, expanded stats

**Mobile Priorities**:
- Bottom navigation for main dashboards
- Collapsible filters/sidebars
- Full-width tables with horizontal scroll
- Touch-friendly targets (min h-12)

## Images

**Hero Image**: Public booking interface should have a compelling hero image (h-64 md:h-96) showing an example screen in an establishment setting. Buttons on hero should have backdrop-blur-sm with semi-transparent backgrounds.

**Screen Thumbnails**: Placeholder images showing example screen installations (cafés, malls, etc.) in establishment dashboards and client interfaces.

**Content Previews**: Actual uploaded content shown in validation queues and reports with proper aspect ratio preservation.

**Empty States**: Illustrations for empty playlists, no bookings, no screens configured.

## Key UX Patterns

**Real-time Updates**: Live status indicators for screens (pulsing dot for online), toast notifications for new bookings/validations.

**Progressive Disclosure**: Show essential info first, expand for details (accordions for advanced settings).

**Contextual Help**: Tooltips on complex fields (resolution requirements, pricing strategy), info icons throughout.

**Feedback**: Clear success/error messages, loading states during async operations, confirmation modals for destructive actions.

**Accessibility**: High contrast ratios, keyboard navigation support, ARIA labels, form validation messages, focus indicators.

This design system balances professional dashboard functionality with consumer-friendly booking experience, ensuring efficiency for power users and ease for occasional clients.