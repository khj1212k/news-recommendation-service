import './globals.css'
import { IBM_Plex_Sans_KR, Nanum_Myeongjo } from 'next/font/google'

const serif = Nanum_Myeongjo({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-serif',
})

const sans = IBM_Plex_Sans_KR({
  subsets: ['latin'],
  weight: ['300', '400', '600', '700'],
  variable: '--font-sans',
})

export const metadata = {
  title: '뉴스 한눈에',
  description: '한국 뉴스 추천 서비스',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={`${serif.variable} ${sans.variable} font-sans`}>
        <div className="page-shell min-h-screen px-6 py-8 md:px-12">
          {children}
        </div>
      </body>
    </html>
  )
}
