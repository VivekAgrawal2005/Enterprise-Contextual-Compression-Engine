import type { Metadata } from 'next'
import './globals.css'
export const metadata: Metadata = { title: 'Enterprise Contextual Compression Engine', description: 'Turn complex documents into verified, decision-critical intelligence.' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html> }
