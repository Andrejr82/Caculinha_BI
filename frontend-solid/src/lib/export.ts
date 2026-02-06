// frontend-solid/src/lib/export.ts

import { format } from 'date-fns';
import { enUS } from 'date-fns/locale';

/**
 * Exports an array of objects to a CSV file.
 * @param data The array of objects to export.
 * @param filename The name of the CSV file.
 */
export const exportToCsv = (data: any[], filename: string) => {
  if (!data || data.length === 0) {
    alert("Nenhum dado para exportar.");
    return;
  }

  // Get headers from the first object's keys
  const headers = Object.keys(data[0]);
  
  // Create CSV header row
  const csvRows = [];
  csvRows.push(headers.join(','));

  // Add data rows
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header];
      // Handle values that might contain commas or newlines
      if (typeof value === 'string' && (value.includes(',') || value.includes('\n'))) {
        return `"${value.replace(/