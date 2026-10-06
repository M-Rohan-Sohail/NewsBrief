export interface SourceTheme {
  primary: string;
  gradient: [string, string, string];
  badgeBg: string;
  badgeBorder: string;
  badgeText: string;
  icon: string;
  tag: string;
  buttonBg: string;
  buttonText: string;
}

export function getSourceTheme(sourceName?: string): SourceTheme {
  const s = (sourceName || '').toLowerCase();
  
  if (s.includes('arxiv')) {
    return {
      primary: '#10B981',
      gradient: ['#064E3B', '#022C22', '#0A0F1D'],
      badgeBg: 'rgba(16, 185, 129, 0.15)',
      badgeBorder: 'rgba(16, 185, 129, 0.4)',
      badgeText: '#34D399',
      icon: '🔬',
      tag: 'ARXIV RESEARCH',
      buttonBg: '#10B981',
      buttonText: '#042F2E'
    };
  }
  
  if (s.includes('github')) {
    return {
      primary: '#A855F7',
      gradient: ['#3B0764', '#1E1B4B', '#0A0F1D'],
      badgeBg: 'rgba(168, 85, 247, 0.15)',
      badgeBorder: 'rgba(168, 85, 247, 0.4)',
      badgeText: '#C084FC',
      icon: '💻',
      tag: 'GITHUB TRENDING',
      buttonBg: '#A855F7',
      buttonText: '#2E1065'
    };
  }
  
  if (s.includes('hacker news') || s.includes('hn')) {
    return {
      primary: '#F97316',
      gradient: ['#431407', '#1C1917', '#0A0F1D'],
      badgeBg: 'rgba(249, 115, 22, 0.15)',
      badgeBorder: 'rgba(249, 115, 22, 0.4)',
      badgeText: '#FB923C',
      icon: '🔶',
      tag: 'HACKER NEWS',
      buttonBg: '#F97316',
      buttonText: '#431407'
    };
  }
  
  // Stratechery, Tech media, or general tech feeds
  return {
    primary: '#EC4899',
    gradient: ['#4C0519', '#1E1B4B', '#0A0F1D'],
    badgeBg: 'rgba(236, 72, 153, 0.15)',
    badgeBorder: 'rgba(236, 72, 153, 0.4)',
    badgeText: '#F472B6',
    icon: '📰',
    tag: (sourceName || 'TECH INTELLIGENCE').toUpperCase(),
    buttonBg: '#EC4899',
    buttonText: '#4C0519'
  };
}
