// src/app/page.tsx
import { Navbar } from '@/components/features/landing/Navbar'
import { HeroSection } from '@/components/features/landing/HeroSection'
import { FeaturesSection } from '@/components/features/landing/FeaturesSection'
import { HowItWorksSection } from '@/components/features/landing/HowItWorksSection'
import { Footer } from '@/components/features/landing/Footer'

export default function HomePage() {
  return (
    <div className="relative">
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <Footer />
    </div>
  )
}
