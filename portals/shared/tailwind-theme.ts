/**
 * Shared Tailwind color theme for all In-Home-Care-Platform portals.
 * Import in each portal's tailwind.config.ts:
 *   import { ihcpColors } from '../../shared/tailwind-theme'
 *   theme: { extend: { colors: ihcpColors } }
 *
 * Design rule: NO gray. NO washed-out light. Bold, warm, high-contrast.
 */
export const ihcpColors = {
  primary: {
    DEFAULT: '#0D7377',
    light: '#11999E',
    dark: '#084C4F',
  },
  secondary: {
    DEFAULT: '#E8612D',
    light: '#F28B5F',
    dark: '#C44A1C',
  },
  background: '#FFFFFF',
  surface: '#F7F9FC',       // very faint blue tint — NOT gray
  text: {
    DEFAULT: '#1A2B3C',
    muted: '#3D5A73',       // blue-leaning, not gray
  },
  success: '#2D8A4E',
  danger: '#D32F2F',
  warning: '#E8A317',
  info: '#1976D2',
  white: '#FFFFFF',
};
