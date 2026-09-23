import { Button, buttonVariants } from '@/components/ui/button'

export interface CtaProps {
  ctaEnabled?: boolean
  text: string
  link?: string
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  onClick?: () => void
}

export function Cta({ cta }: { cta: CtaProps }) {
  if (!cta || cta.ctaEnabled === false) return null

  if (cta.link) {
    return (
      <a
        href={cta.link}
        className={buttonVariants({ variant: cta.variant ?? 'default', size: cta.size ?? 'default' })}
      >
        {cta.text}
      </a>
    )
  }

  return (
    <Button variant={cta.variant ?? 'default'} size={cta.size ?? 'default'} onClick={cta.onClick}>
      {cta.text}
    </Button>
  )
}
