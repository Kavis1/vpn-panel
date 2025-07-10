import { format } from 'date-fns';
import { formatDistanceToNow } from 'date-fns/formatDistanceToNow';

/**
 * Format bytes to a human-readable string
 * @param bytes - The number of bytes
 * @param decimals - Number of decimal places
 * @returns Formatted string with appropriate unit (B, KB, MB, GB, etc.)
 */
export const formatBytes = (bytes: number = 0, decimals: number = 2): string => {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

/**
 * Format a date string to a localized date format
 * @param dateString - ISO date string
 * @returns Formatted date string (e.g., "12 января 2023 г.")
 */
export const formatDate = (dateString: string): string => {
  try {
    return format(new Date(dateString), 'd MMMM yyyy г.');
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateString; // Return original string if formatting fails
  }
};

/**
 * Format a date string to a localized date and time format
 * @param dateString - ISO date string
 * @returns Formatted date and time string (e.g., "12 января 2023 г., 14:30")
 */
export const formatDateTime = (dateString: string): string => {
  try {
    return format(new Date(dateString), 'd MMMM yyyy г., HH:mm');
  } catch (error) {
    console.error('Error formatting date and time:', error);
    return dateString; // Return original string if formatting fails
  }
};

/**
 * Format distance to now (e.g., "2 hours ago")
 */
export const formatDistanceToNowSafe = (date: Date | string): string => {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return formatDistanceToNow(dateObj, { addSuffix: true });
  } catch (error) {
    console.error('Error formatting distance to now:', error);
    return 'Unknown time';
  }
};

/**
 * Format a duration in seconds to a human-readable string
 * @param seconds - Duration in seconds
 * @returns Formatted duration string (e.g., "2 часа 30 минут")
 */
export const formatDuration = (seconds: number): string => {
  if (!seconds && seconds !== 0) return 'Н/Д';
  
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  const parts = [];
  
  if (days > 0) {
    parts.push(`${days} ${getRussianNoun(days, ['день', 'дня', 'дней'])}`);
  }
  
  if (hours > 0) {
    parts.push(`${hours} ${getRussianNoun(hours, ['час', 'часа', 'часов'])}`);
  }
  
  if (minutes > 0 && days === 0) {
    parts.push(`${minutes} ${getRussianNoun(minutes, ['минута', 'минуты', 'минут'])}`);
  }
  
  if (seconds < 3600) { // Only show seconds for durations less than an hour
    parts.push(`${remainingSeconds} ${getRussianNoun(remainingSeconds, ['секунда', 'секунды', 'секунд'])}`);
  }
  
  return parts.length > 0 ? parts.join(' ') : '0 секунд';
};

/**
 * Helper function to get the correct Russian noun form based on the count
 * @param number - The count
 * @param forms - Array of three forms: [one, few, many]
 * @returns The correct form of the noun
 */
const getRussianNoun = (number: number, forms: [string, string, string]): string => {
  const n = Math.abs(number) % 100;
  const n1 = n % 10;
  
  if (n > 10 && n < 20) return forms[2];
  if (n1 > 1 && n1 < 5) return forms[1];
  if (n1 === 1) return forms[0];
  return forms[2];
};

/**
 * Format a number with thousands separators
 * @param num - The number to format
 * @returns Formatted number string with spaces as thousand separators
 */
export const formatNumber = (num: number): string => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
};

/**
 * Format a price with currency
 * @param amount - The amount to format
 * @param currency - Currency code (default: 'RUB')
 * @returns Formatted price string
 */
export const formatPrice = (amount: number, currency: string = 'RUB'): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Truncate a string with an ellipsis if it exceeds the max length
 * @param str - The string to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated string with ellipsis if needed
 */
export const truncateString = (str: string, maxLength: number = 50): string => {
  if (!str) return '';
  return str.length > maxLength ? `${str.substring(0, maxLength)}...` : str;
};
