# Theme Integration Guide - UserManagement WebUI

This guide explains how the UserManagement WebUI implements theming using Tailwind CSS and how external applications can integrate with and listen to theme changes.

## Overview

The UserManagement WebUI uses **Tailwind CSS** with a class-based dark mode strategy for theming. This provides:
- Native Tailwind dark mode support
- Easy integration with external applications
- Consistent theme across all pages
- Simple theme switching mechanism

## Theme System Architecture

### Supported Themes

1. **Light Theme** (default)
   - No class needed on `<html>` element
   - Uses standard Tailwind colors with custom theme palette

2. **Dark Theme**
   - Class `dark` on `<html>` element
   - Uses dark-optimized color palette

3. **High Contrast Theme**
   - Class `high-contrast` on `<html>` element
   - Uses high contrast black/white palette for accessibility

### Core Components

#### 1. Tailwind Configuration (`tailwind.config.js`)

```javascript
module.exports = {
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        'theme': { /* light mode colors */ },
        'theme-dark': { /* dark mode colors */ },
        'theme-contrast': { /* high contrast colors */ }
      }
    }
  }
}
```

#### 2. Theme Service (`theme.service.ts`)

The `ThemeService` manages theme state and applies theme classes:

```typescript
export enum Theme {
  LIGHT = 'light',
  DARK = 'dark',
  HIGH_CONTRAST = 'high-contrast'
}

// Key methods:
setTheme(theme: Theme): void
getCurrentTheme(): Theme
currentTheme$: Observable<Theme>
```

#### 3. Global Styles (`styles.scss`)

Provides CSS custom properties for backwards compatibility and base styling.

## How Themes Work

### Theme Application Flow

1. User selects theme via `ThemeSwitcher` component
2. `ThemeService.setTheme()` is called
3. Theme preference is saved to `localStorage` (key: `user-theme`)
4. Theme class is applied to `<html>` element:
   - Light: no class
   - Dark: `class="dark"`
   - High Contrast: `class="high-contrast"`
5. Tailwind's dark mode utilities automatically apply appropriate styles

### Using Theme Colors in Components

Components use Tailwind utility classes with theme colors:

```html
<!-- Light mode: bg-theme-surface, Dark mode: automatic -->
<div class="bg-theme-surface text-theme-text border border-theme-border">
  <button class="bg-theme-primary hover:bg-theme-primary-hover text-theme-primary-text">
    Click me
  </button>
</div>
```

For dark mode overrides, use Tailwind's `dark:` prefix:

```html
<div class="bg-white dark:bg-gray-800 text-black dark:text-white">
  Content
</div>
```

## Integrating External Applications

### Option 1: Query Parameter Integration

External apps can pass theme preferences via URL parameters:

```
https://usermgmt-app.com/login?theme=dark
```

**Implementation in External App:**

```typescript
// External app redirects with theme
const currentTheme = localStorage.getItem('app-theme') || 'light';
window.location.href = `https://usermgmt-app.com/login?theme=${currentTheme}&redirect_uri=${encodeURIComponent(callbackUrl)}`;
```

**Implementation in UserManagement App:**

```typescript
// In app initialization or login component
ngOnInit() {
  const params = new URLSearchParams(window.location.search);
  const themeParam = params.get('theme');
  if (themeParam && ['light', 'dark', 'high-contrast'].includes(themeParam)) {
    this.themeService.setTheme(themeParam as Theme);
  }
}
```

### Option 2: Shared Tailwind Config Package

For multiple Angular applications sharing the same theme:

1. **Create a shared npm package:**

```bash
npm init @your-org/tailwind-config
```

2. **Export tailwind.config.js:**

```javascript
// @your-org/tailwind-config/tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // shared theme colors
      }
    }
  }
}
```

3. **Use in consuming apps:**

```javascript
// External app's tailwind.config.js
const sharedConfig = require('@your-org/tailwind-config');

module.exports = {
  ...sharedConfig,
  content: [
    "./src/**/*.{html,ts}",
  ],
}
```

### Option 3: CDN-Hosted Theme Stylesheet

For cross-framework integration:

1. **Export theme as CSS:**

```bash
# Build theme CSS
npm run build:css
# Output: theme.css with all theme variables
```

2. **Host on CDN:**

```html
<!-- External app loads theme -->
<link rel="stylesheet" href="https://cdn.your-org.com/themes/v1/theme.css">
```

3. **Sync theme via postMessage:**

```javascript
// External app listens for theme changes
window.addEventListener('message', (event) => {
  if (event.data.type === 'theme-change') {
    document.documentElement.className = event.data.theme === 'dark' ? 'dark' : '';
  }
});

// UserManagement app posts theme changes
window.parent.postMessage({ type: 'theme-change', theme: 'dark' }, '*');
```

### Option 4: Shared ThemeService Library

Create an Angular library with the ThemeService:

```bash
ng generate library @your-org/theme
```

Both apps import and use the shared service, ensuring synchronized theme state.

## Theme Colors Reference

### Light Theme Colors

| Purpose | Tailwind Class | RGB Value | Hex |
|---------|---------------|-----------|-----|
| Primary | `bg-theme-primary` | rgb(37 99 235) | #2563eb |
| Background | `bg-theme-background` | rgb(244 247 246) | #f4f7f6 |
| Surface | `bg-theme-surface` | rgb(255 255 255) | #ffffff |
| Text | `text-theme-text` | rgb(51 51 51) | #333333 |
| Border | `border-theme-border` | rgb(209 213 219) | #d1d5db |

### Dark Theme Colors

| Purpose | Tailwind Class | RGB Value | Hex |
|---------|---------------|-----------|-----|
| Primary | `bg-theme-dark-primary` | rgb(14 165 233) | #0ea5e9 |
| Background | `bg-theme-dark-background` | rgb(15 23 42) | #0f172a |
| Surface | `bg-theme-dark-surface` | rgb(30 41 59) | #1e293b |
| Text | `text-theme-dark-text` | rgb(241 245 249) | #f1f5f9 |
| Border | `border-theme-dark-border` | rgb(71 85 105) | #475569 |

### High Contrast Theme Colors

| Purpose | Tailwind Class | RGB Value | Hex |
|---------|---------------|-----------|-----|
| Primary | `bg-theme-contrast-primary` | rgb(0 0 0) | #000000 |
| Background | `bg-theme-contrast-background` | rgb(255 255 255) | #ffffff |
| Text | `text-theme-contrast-text` | rgb(0 0 0) | #000000 |
| Border | `border-theme-contrast-border` | rgb(0 0 0) | #000000 |

## Best Practices

### For UserManagement App Developers

1. **Always use theme utility classes** instead of hardcoded colors
2. **Test all themes** before deploying
3. **Provide fallbacks** for unsupported browsers
4. **Document custom theme extensions** in this guide

### For External App Developers

1. **Match the theme system** if possible (use same Tailwind config)
2. **Handle theme sync errors gracefully**
3. **Cache theme preference** in localStorage
4. **Provide theme override option** for users

## Theme Switcher Component

The UserManagement app includes a `ThemeSwitcher` component that can be embedded in any page:

```html
<app-theme-switcher></app-theme-switcher>
```

This component:
- Shows current theme
- Provides dropdown to select themes
- Automatically syncs with ThemeService
- Persists selection to localStorage

## Testing Themes

### Manual Testing

1. Open the app in different browsers
2. Use the theme switcher to change themes
3. Verify all pages reflect the theme
4. Check localStorage for persisted theme

### Automated Testing

```typescript
describe('ThemeService', () => {
  it('should switch to dark theme', () => {
    themeService.setTheme(Theme.DARK);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
```

## Troubleshooting

### Theme not applying

- Check if Tailwind CSS is properly loaded
- Verify `darkMode: 'class'` is set in `tailwind.config.js`
- Ensure `<html>` element has the correct class

### Theme not persisting

- Check localStorage for `user-theme` key
- Verify ThemeService is initialized in app constructor
- Clear browser cache and try again

### External app theme sync issues

- Verify CORS settings allow postMessage
- Check that theme parameter is properly encoded in URL
- Ensure both apps use compatible theme systems

## Future Enhancements

- [ ] Add more theme variants (blue, green, etc.)
- [ ] Support system theme preference auto-detection
- [ ] Create Storybook for theme documentation
- [ ] Add theme preview before applying
- [ ] Support custom theme colors from API

## Support

For questions or issues related to theming:
- Check this guide first
- Review Tailwind CSS documentation: https://tailwindcss.com/docs/dark-mode
- Contact the development team

---

**Version:** 1.0  
**Last Updated:** October 10, 2025  
**Maintainer:** UserManagement Development Team
