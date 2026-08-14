import { i18n, type Language } from '../i18n';

export interface BlockI18nData {
  display_name?: string;
  name?: string;
  description?: string;
  category?: string;
  pins?: Record<string, string>;
  properties?: Record<string, string>;
}

export interface BlockSchemaLike {
  name?: string;
  display_name?: string;
  description?: string;
  category?: string;
  i18n?: Record<string, BlockI18nData>;
  dataIns?: Array<{ name: string; label?: string; [key: string]: any }>;
  dataOuts?: Array<{ name: string; label?: string; [key: string]: any }>;
  execIns?: string[];
  execOuts?: string[];
}

/**
 * Resolves localized block title (display name).
 */
export function getBlockTitle(block: BlockSchemaLike, lang?: Language): string {
  const activeLang = lang || i18n.language;
  if (block.i18n?.[activeLang]?.display_name || block.i18n?.[activeLang]?.name) {
    return (block.i18n[activeLang].display_name || block.i18n[activeLang].name)!;
  }
  if (block.i18n?.['en']?.display_name || block.i18n?.['en']?.name) {
    return (block.i18n['en'].display_name || block.i18n['en'].name)!;
  }
  return block.display_name || block.name || 'Block';
}

/**
 * Resolves localized block description.
 */
export function getBlockDescription(block: BlockSchemaLike, lang?: Language): string {
  const activeLang = lang || i18n.language;
  if (block.i18n?.[activeLang]?.description) {
    return block.i18n[activeLang].description!;
  }
  if (block.i18n?.['en']?.description) {
    return block.i18n['en'].description!;
  }
  return block.description || '';
}

/**
 * Resolves localized block category.
 */
export function getBlockCategory(block: BlockSchemaLike, lang?: Language): string {
  const activeLang = lang || i18n.language;
  if (block.i18n?.[activeLang]?.category) {
    return block.i18n[activeLang].category!;
  }
  return block.category || 'Logic';
}

/**
 * Resolves localized pin label (inputs/outputs).
 */
export function getPinLabel(block: BlockSchemaLike, pinName: string, lang?: Language): string {
  const activeLang = lang || i18n.language;
  if (block.i18n?.[activeLang]?.pins?.[pinName]) {
    return block.i18n[activeLang].pins![pinName];
  }
  if (block.i18n?.['en']?.pins?.[pinName]) {
    return block.i18n['en'].pins![pinName];
  }
  return pinName;
}

/**
 * Resolves localized property / parameter label in Block Inspector.
 */
export function getPropertyLabel(block: BlockSchemaLike, propKey: string, lang?: Language): string {
  const activeLang = lang || i18n.language;
  if (block.i18n?.[activeLang]?.properties?.[propKey]) {
    return block.i18n[activeLang].properties![propKey];
  }
  if (block.i18n?.['en']?.properties?.[propKey]) {
    return block.i18n['en'].properties![propKey];
  }
  // Convert camelCase / snake_case to Title Case if no translation
  return propKey
    .replace(/([A-Z])/g, ' $1')
    .replace(/_/g, ' ')
    .replace(/^./, (str) => str.toUpperCase());
}
