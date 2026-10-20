<!-- Task T1: Gather UI/UX requirements and layout specifications for a YouTube frontend clone, including navigation sidebar, video feed grid, search bar, and video player modal structure. -->

### 1. Global Layout & Structure

*   **Grid Framework:** Use a fixed top navigation bar and a flex/grid-based main body split into a collapsible sidebar and a fluid content area.
*   **Color Palette (Dark Mode standard as reference):**
    *   Background (App): `#0f0f0f`
    *   Surface (Sidebar/Nav/Cards): `#212121`
    *   Text Primary: `#f1f1f1`
    *   Text Secondary: `#aaa`
    *   Accent: `#3ea6ff` (YouTube Blue) or `#ff0000` (YouTube Brand Red)
*   **Typography:** Roboto, Arial, sans-serif.

---

### 2. Navigation Components

#### A. Top Navigation Bar (Header)
*   **Layout:** Fixed position (`position: fixed; top: 0; width: 100%; z-index: 100`), flexbox row, space-between alignment, height: 56px, background matching app surface.
*   **Left Section:**
    *   Menu/Hamburger Icon: Toggles sidebar state (expanded vs. collapsed/mini).
    *   YouTube Logo: SVG icon (Red play button + typography), links to home (`/`).
*   **Center Section (Search Bar):**
    *   Flex-grow container, centered.
    *   Input Field: Rounded-left border, dark background (`#121212`), light grey border (`#303030`), placeholder "Search", text color `#fff`.
    *   Search Button: Rounded-right border, matching border, neutral grey background (`#222`), magnifying glass icon.
    *   Mic Button: Circular icon button (`#181818`), voice search trigger.
*   **Right Section:**
    *   Create/Upload Icon (Camera + `+` symbol).
    *   Notifications Icon (Bell) with unread badge counter.
    *   User Avatar: Circular, 32px diameter, links to account menu.

#### B. Navigation Sidebar
*   **Behavior:** 
    *   Desktop (Expanded): Width ~240px.
    *   Desktop (Collapsed/Mini): Width ~72px (shows icons only with stacked labels).
    *   Mobile: Hidden off-screen, triggered via overlay drawer.
*   **Structure & Grouping (Divided by subtle horizontal borders):**
    *   *Group 1:* Home, Shorts, Subscriptions.
    *   *Group 2 (Library):* You (Channel), History, Your Videos, Watch Later, Liked Videos.
    *   *Group 3 (Subscriptions List):* Avatars + Channel Names (truncated with ellipsis).
    *   *Group 4 (Explore/More):* Trending, Music, Gaming, News, Sports.
    *   *Footer:* Copyright, Meta links (Terms, Privacy).

---

### 3. Video Feed Grid (Home Page)

#### A. Category/Chips Bar
*   **Layout:** Horizontal scrolling flex container pinned below the top navigation bar.
*   **Items:** Pill-shaped buttons (`border-radius: 8px`), padding `6px 12px`, background `#272727` (default) switching to `#f1f1f1` with `#0f0f0f` text when active ("All", "Gaming", "Live", "Music", etc.).
*   **Behavior:** Sticky positioning just below the header.

#### B. Video Card Component
*   **Grid Layout:** CSS Grid (`grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`), gap: 16px row, 16px column.
*   **Card Structure:**
    1.  **Thumbnail Container:**
        *   Aspect Ratio: 16:9, `border-radius: 12px`, relative positioning.
        *   Overlay (Bottom-Right): Timestamp badge (e.g., "14:22"), dark background, 4px border-radius, white text, 12px font.
        *   Interaction: Hover state scales thumbnail slightly or triggers a video preview (if implemented); show "Watch Later" and "Add to Queue" quick-action icons on hover.
    2.  **Metadata Section:**
        *   Layout: Flex row, `gap: 12px`, `margin-top: 12px`.
        *   Channel Avatar: Circular, 36px diameter, flex-shrink: 0.
        *   Text Details (Flex column):
            *   *Video Title:* 2-line clamp (`display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;`), 14px font, bold, text primary.
            *   *Channel Name:* 12px font, text secondary, checkmark icon for verified channels.
            *   *Metrics:* Views count + "•" + Relative time (e.g., "125K views • 2 days ago"), 12px font, text secondary.

---

### 4. Video Player Modal / Watch Page Structure

*   **Layout Archetype:** Asymmetric 2-column layout on desktop (Primary video column + Secondary recommendations sidebar).
*   **Left Column (Player & Metadata):**
    *   **Video Player:** 16:9 responsive container. Standard controls (play/pause, timeline scrubber, volume, captions, settings, pip, fullscreen).
    *   **Metadata:**
        *   Title: Large font (18px), bold.
        *   Channel Row: Avatar + Name + Subscriber Count + Subscribe Button (High contrast pill: white background, black text).
        *   Action Bar (Right side of channel row): Like/Dislike (joined pill), Share, Download, Clip, Save.
    *   **Description Box:**
        *   Rounded container, background `#272727`.
        *   Collapsible: Shows views, upload date, and first 3 lines of text by default; expands on click. Hashtags highlighted in blue.
    *   **Comments Section:**
        *   Header: "X Comments" + Sort by dropdown.
        *   Input: User avatar + text input with bottom border ("Add a comment...").
        *   Comment Threads: Avatar, Author name, time, comment body, like/dislike buttons, reply action, nested replies toggle.
*   **Right Column (Recommendations):**
    *   Vertical stack of horizontal video cards.
    *   Thumbnail: Smaller (approx. 168px wide), left-aligned.
    *   Metadata: Right of thumbnail (Title, Channel, Views/Time stacked, smaller text scaling).

---

### 5. Uncertainty & Ambiguities Note

*   *Uncertainty:* Exact implementation details for dynamic features (e.g., infinite scroll pagination thresholds, real-time comment fetching, and the exact proprietary hover-preview video-switching logic) are not officially documented by YouTube and must be approximated through heuristics or custom frontend logic.
