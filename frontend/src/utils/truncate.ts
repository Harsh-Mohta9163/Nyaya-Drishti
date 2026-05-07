/**
 * Truncates a string to maxLen, prioritizing splitting at a space so we don't cut words in half.
 */
export function truncateName(name: string, maxLen: number = 60): string {
  if (!name) return '—';
  if (name.length <= maxLen) return name;
  const sub = name.substring(0, maxLen);
  const lastSpace = sub.lastIndexOf(' ');
  if (lastSpace > 0) {
    return sub.substring(0, lastSpace) + '…';
  }
  return sub + '…';
}

/**
 * Given a long legal party name (e.g., "SRI H.S. GAURAV S/O H.G. SOMASHEKAR REDDY AGED ABOUT 28 YEARS...")
 * attempts to extract just the core name before any descriptive clauses.
 */
export function extractCoreName(fullName: string): string {
  if (!fullName) return '';
  
  // Convert to Title Case for better readability
  const titleCased = fullName.toLowerCase().replace(/\b\w/g, s => s.toUpperCase());
  
  // Split on common legal descriptors
  const splitTokens = [' S/o ', ' D/o ', ' W/o ', ' Aged ', ' Represented By ', ' Rep. By ', ','];
  
  let coreName = titleCased;
  for (const token of splitTokens) {
    // case-insensitive split
    const parts = coreName.split(new RegExp(token, 'i'));
    if (parts.length > 1) {
      coreName = parts[0];
    }
  }
  
  return truncateName(coreName.trim(), 40);
}

/**
 * Creates a clean "Petitioner vs. Respondent" string.
 */
export function shortPartyTitle(petitioner?: string, respondent?: string): string {
  const p = extractCoreName(petitioner || '');
  const r = extractCoreName(respondent || '');
  
  if (p && r) return `${p} vs. ${r}`;
  if (p) return p;
  if (r) return r;
  return 'Unknown Parties';
}

/**
 * Handles concatenated case numbers (e.g. "WP No. 27824 of 2025 C/W WP No. 27595 of 2025")
 * Returns an object with the primary case number and the count of additional cases.
 */
export function formatCaseNumber(caseNum: string): { primary: string, additionalCount: number } {
  if (!caseNum) return { primary: '—', additionalCount: 0 };
  
  // Split on common concatenators like "C/W" (connected with), "A/W" (along with)
  const parts = caseNum.split(/ c\/w | a\/w /i).map(p => p.trim()).filter(Boolean);
  
  if (parts.length === 0) return { primary: '—', additionalCount: 0 };
  if (parts.length === 1) return { primary: truncateName(parts[0], 30), additionalCount: 0 };
  
  return { 
    primary: truncateName(parts[0], 30), 
    additionalCount: parts.length - 1 
  };
}
